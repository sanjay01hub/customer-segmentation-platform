import re
import numpy as np
import pandas as pd

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _r(x, n=0):
    return round(float(x), n)


# ---------------------------------------------------------------- overview
def overview(df):
    out = {
        "revenue": _r(df["TotalPrice"].sum()),
        "orders": int(df["InvoiceNo"].nunique()),
        "units": int(df["Quantity"].sum()),
        "date_from": df["InvoiceDate"].min().strftime("%d %b %Y"),
        "date_to": df["InvoiceDate"].max().strftime("%d %b %Y"),
        "avg_order": _r(df["TotalPrice"].sum() / max(df["InvoiceNo"].nunique(), 1)),
        "products": int(df["Product"].nunique()) if "Product" in df.columns else None,
        "customers": int(df["CustomerID"].nunique()) if "CustomerID" in df.columns else None,
    }
    if "Product" in df.columns:
        top = (df.groupby("Product")["TotalPrice"].sum()
               .sort_values(ascending=False).head(10))
        out["top_products"] = [{"name": k, "revenue": _r(v)} for k, v in top.items()]
    if "Country" in df.columns:
        c = df.groupby("Country")["TotalPrice"].sum().sort_values(ascending=False).head(8)
        out["top_countries"] = [{"name": str(k), "revenue": _r(v)} for k, v in c.items()]
    return out


# ---------------------------------------------------------------- products
def _slow_reason(row, median_price, span_days):
    """Guess why a slow product is not selling and suggest a fix."""
    reasons, ideas = [], []
    if row["days_since"] > max(45, span_days * 0.4):
        reasons.append("No recent sales: it may be out of season or forgotten")
        ideas.append("Run a clearance sale, or bring it back onto the homepage / shelf front")
    if row["price"] > median_price * 1.5:
        reasons.append("Priced higher than most of your products")
        ideas.append("Try a limited-time discount or a 'buy 2, save more' offer")
    if row["orders"] <= 3:
        reasons.append("Very few customers have bought it")
        ideas.append("Bundle it with a fast-moving product so more people see it")
    if row["peak_share"] >= 0.5 and row["orders"] > 3:
        reasons.append("Sells mostly in one season")
        ideas.append("Keep stock low now and promote it before its peak months")
    if not reasons:
        reasons.append("Steady but low interest")
        ideas.append("Improve its display or description and test a small discount")
    return "; ".join(reasons), "; ".join(dict.fromkeys(ideas))


def product_movement(df):
    if "Product" not in df.columns:
        return None
    end = df["InvoiceDate"].max()
    span_days = max((end - df["InvoiceDate"].min()).days, 1)
    g = df.groupby("Product")
    p = pd.DataFrame({
        "units": g["Quantity"].sum(),
        "revenue": g["TotalPrice"].sum(),
        "orders": g["InvoiceNo"].nunique(),
        "price": g["UnitPrice"].median(),
        "last": g["InvoiceDate"].max(),
    })
    p["days_since"] = (end - p["last"]).dt.days
    month_units = df.groupby(["Product", df["InvoiceDate"].dt.month])["Quantity"].sum().unstack(fill_value=0)
    p["peak_share"] = (month_units.max(axis=1) / month_units.sum(axis=1)).reindex(p.index)
    p["per_month"] = p["units"] / max(span_days / 30.0, 1)

    # stock column: use the latest value per product
    has_stock = "Stock" in df.columns
    if has_stock:
        s = pd.to_numeric(df.sort_values("InvoiceDate").groupby("Product")["Stock"].last(), errors="coerce")
        p["stock"] = s
        p["cover_days"] = p["stock"] / (p["units"] / span_days)

    q75, q25 = p["units"].quantile(0.75), p["units"].quantile(0.25)
    dormant = p["days_since"] > max(45, span_days * 0.4)

    def label(i, r):
        if r["units"] >= q75 and not dormant[i]:
            return "Fast"
        if r["units"] <= q25 or dormant[i]:
            return "Slow"
        return "Medium"
    p["movement"] = [label(i, r) for i, r in p.iterrows()]

    # recent trend: last 30 days vs the overall average rate (for stock-out risk)
    recent = df[df["InvoiceDate"] > end - pd.Timedelta(days=30)].groupby("Product")["Quantity"].sum()
    p["recent"] = recent.reindex(p.index).fillna(0)
    p["trend"] = p["recent"] / p["per_month"].replace(0, np.nan)

    counts = p["movement"].value_counts().to_dict()
    fast = p[p["movement"] == "Fast"].sort_values("units", ascending=False).head(15)
    slow = p[p["movement"] == "Slow"].sort_values("units").head(15)
    median_price = p["price"].median()

    slow_rows = []
    for name, r in slow.iterrows():
        why, idea = _slow_reason(r, median_price, span_days)
        slow_rows.append({"name": name, "units": int(r["units"]), "orders": int(r["orders"]),
                          "days_since": int(r["days_since"]), "why": why, "idea": idea})

    # low stock / stock-out risk
    if has_stock and p["stock"].notna().any():
        risky = p[(p["movement"] != "Slow") & (p["cover_days"] < 14)].sort_values("cover_days").head(15)
        low = [{"name": n, "stock": int(r["stock"]), "cover": _r(r["cover_days"], 1),
                "units": int(r["units"]),
                "note": "Reorder now: stock covers less than %d days of sales" % max(int(r["cover_days"]), 1)}
               for n, r in risky.iterrows()]
        low_mode = "stock"
    else:
        risky = p[(p["movement"] == "Fast") & (p["trend"] > 1.2)].sort_values("trend", ascending=False).head(15)
        low = [{"name": n, "stock": None, "cover": None, "units": int(r["units"]),
                "note": "Sales in the last 30 days are %.1fx the usual rate. Check stock and reorder early." % r["trend"]}
               for n, r in risky.iterrows()]
        low_mode = "trend"

    return {
        "counts": {"Fast": int(counts.get("Fast", 0)), "Medium": int(counts.get("Medium", 0)),
                   "Slow": int(counts.get("Slow", 0))},
        "fast": [{"name": n, "units": int(r["units"]), "revenue": _r(r["revenue"]),
                  "per_month": _r(r["per_month"], 1)} for n, r in fast.iterrows()],
        "slow": slow_rows,
        "low_stock": low,
        "low_mode": low_mode,
    }


# ---------------------------------------------------------------- demand
def _forecast(series):
    """Very simple forecast: blend of the 3-month average and the recent trend."""
    v = np.array(series, dtype=float)
    if len(v) < 3:
        return None
    base = v[-3:].mean()
    recent = v[-6:]
    slope = np.polyfit(np.arange(len(recent)), recent, 1)[0] if len(recent) >= 3 else 0
    return max(0.0, 0.5 * base + 0.5 * (recent[-1] + slope))


def demand(df):
    d = df.copy()
    d["Month"] = d["InvoiceDate"].dt.to_period("M")
    monthly = d.groupby("Month").agg(units=("Quantity", "sum"), revenue=("TotalPrice", "sum"))
    last_ts = d["InvoiceDate"].max()
    # drop the last month if it is incomplete
    if len(monthly) > 3 and last_ts.day < last_ts.days_in_month - 2:
        monthly = monthly.iloc[:-1]
    labels = [str(m) for m in monthly.index]

    out = {
        "months": labels,
        "month_units": [int(x) for x in monthly["units"]],
        "month_revenue": [_r(x) for x in monthly["revenue"]],
    }
    fu = _forecast(monthly["units"])
    out["forecast_units"] = None if fu is None else int(round(fu))
    if len(monthly):
        nxt = (monthly.index[-1] + 1)
        out["forecast_month"] = str(nxt)

    # best months of the year (needs data from more than one month)
    moy = d.groupby(d["InvoiceDate"].dt.month)["Quantity"].sum()
    out["moy"] = [int(moy.get(i, 0)) for i in range(1, 13)]
    if len(moy) > 1:
        out["best_months"] = [MONTHS[i - 1] for i in moy.sort_values(ascending=False).head(3).index]

    wd = d.groupby(d["InvoiceDate"].dt.dayofweek)["Quantity"].sum()
    out["weekday"] = [int(wd.get(i, 0)) for i in range(7)]
    out["best_day"] = DAYS[int(wd.idxmax())]

    if (d["InvoiceDate"].dt.hour != 0).any():
        hr = d.groupby(d["InvoiceDate"].dt.hour)["Quantity"].sum()
        out["hour"] = [int(hr.get(i, 0)) for i in range(24)]
        out["best_hours"] = [f"{h}:00" for h in hr.sort_values(ascending=False).head(3).index]

    # product-wise demand and selling window
    if "Product" in d.columns:
        top = d.groupby("Product")["Quantity"].sum().sort_values(ascending=False).head(8).index
        rows = []
        for name in top:
            pdx = d[d["Product"] == name]
            pm = pdx.groupby("Month")["Quantity"].sum().reindex(monthly.index, fill_value=0)
            f = _forecast(pm)
            pmoy = pdx.groupby(pdx["InvoiceDate"].dt.month)["Quantity"].sum().sort_values(ascending=False)
            pday = pdx.groupby(pdx["InvoiceDate"].dt.dayofweek)["Quantity"].sum()
            trend = ""
            if f is not None and pm.iloc[-3:].mean() > 0:
                ratio = f / pm.iloc[-3:].mean()
                trend = "Rising" if ratio > 1.1 else "Falling" if ratio < 0.9 else "Steady"
            rows.append({
                "name": name,
                "forecast": None if f is None else int(round(f)),
                "trend": trend,
                "peak_months": ", ".join(MONTHS[i - 1] for i in pmoy.head(2).index) if len(pmoy) > 1 else "-",
                "best_day": DAYS[int(pday.idxmax())],
            })
        out["products"] = rows
    return out


# ---------------------------------------------------------------- who buys what
GROUPS = [
    ("Children", r"\b(?:kid|kids|child|children|childs|baby|babies|toy|toys|doll|dolls|nursery|"
                 r"school|teddy|crayon|crayons|lunch ?box|girls|boys|puzzle|playing|rattle|bib)\b"),
    ("Men", r"\b(?:men|mens|man|gent|gents|gentleman|beard|shaving|cufflink|cufflinks|tie|"
            r"toolbox|tool|beer|whisky|wallet)\b"),
    ("Women", r"\b(?:women|womens|woman|lady|ladies|handbag|bag|purse|necklace|earring|earrings|"
              r"bracelet|jewellery|jewelry|perfume|makeup|scarf|dress|bangle|tiara|hairclip|"
              r"candle|candles|floral|heart)\b"),
    ("Elderly", r"\b(?:senior|elderly|walking|stick|reading|glasses|magnifying|slipper|slippers|"
                r"comfort|pill|hot ?water|blanket|cushion)\b"),
]


def audience(df):
    if "Product" not in df.columns:
        return None
    g = df.groupby("Product").agg(units=("Quantity", "sum"), revenue=("TotalPrice", "sum"))
    names = g.index.to_series()
    group = pd.Series("General / both", index=g.index)
    assigned = pd.Series(False, index=g.index)
    lowered = names.str.lower()
    for label, pattern in GROUPS:
        hit = lowered.str.contains(pattern, regex=True) & ~assigned
        group[hit] = label
        assigned |= hit
    g["Group"] = group
    rows = []
    total_rev = g["revenue"].sum()
    for label in ["Children", "Men", "Women", "Elderly", "General / both"]:
        sub = g[g["Group"] == label].sort_values("revenue", ascending=False)
        rows.append({
            "group": label,
            "products": int(len(sub)),
            "units": int(sub["units"].sum()),
            "revenue": _r(sub["revenue"].sum()),
            "share": _r(sub["revenue"].sum() / total_rev * 100, 1) if total_rev else 0,
            "top": [{"name": n, "revenue": _r(r["revenue"])} for n, r in sub.head(5).iterrows()],
        })
    return rows


# ---------------------------------------------------------------- health score
from translate import MONTHS_TA  # noqa: E402

_H = {
    "en": {
        "labels": ("Healthy", "Okay", "Needs attention"),
        "parts": {"customers": "Customers", "products": "Products", "demand": "Demand"},
        "risk": "Send a win-back offer to your {n} at-risk customers.",
        "champ": "Thank your {n} best customers and give them early access to new items.",
        "low": "Check stock and reorder {name} today.",
        "slow": "Put {name} on offer or bundle it with {fast}.",
        "slow_alone": "Put {name} on offer or move it to the front of the shop.",
        "peak": "Stock up and advertise before {months}, your best selling months.",
    },
    "ta": {
        "labels": ("நல்ல நிலை", "சராசரி", "கவனம் தேவை"),
        "parts": {"customers": "வாடிக்கையாளர்கள்", "products": "பொருட்கள்", "demand": "தேவை"},
        "risk": "இழக்கும் அபாயத்தில் உள்ள உங்கள் {n} வாடிக்கையாளர்களுக்கு மீண்டும் வர சலுகை அனுப்புங்கள்.",
        "champ": "உங்கள் {n} சிறந்த வாடிக்கையாளர்களுக்கு நன்றி சொல்லி, புதிய பொருட்களை முதலில் வாங்கும் வாய்ப்பு கொடுங்கள்.",
        "low": "{name} இருப்பைச் சரிபார்த்து இன்றே மீண்டும் ஆர்டர் செய்யுங்கள்.",
        "slow": "{name} பொருளுக்குச் சலுகை கொடுங்கள் அல்லது {fast} உடன் சேர்த்து விற்கவும்.",
        "slow_alone": "{name} பொருளுக்குச் சலுகை கொடுங்கள் அல்லது கடையின் முன்பகுதியில் வையுங்கள்.",
        "peak": "{months} உங்கள் அதிகம் விற்கும் மாதங்கள்; அதற்கு முன் இருப்பு வைத்து விளம்பரம் செய்யுங்கள்.",
    },
}


def _clamp(x):
    return max(0, min(100, x))


def health(r, lang="en"):
    """Score 0-100 from whatever sections the file allowed, plus a short action list."""
    T = _H["ta" if lang == "ta" else "en"]
    parts, actions = [], []

    seg = r.get("segmentation")
    if seg:
        share = {"good": 0.0, "mid": 0.0, "risk": 0.0}
        risk_n = champ_n = 0
        for s in seg["segments"]:
            name = s["Segment"]
            if name.startswith(("Champions", "Loyal")):
                share["good"] += s["Share"]
            elif name.startswith("At-risk"):
                share["risk"] += s["Share"]
                risk_n += int(s["Customers"])
            else:
                share["mid"] += s["Share"]
            if name.startswith("Champions"):
                champ_n += int(s["Customers"])
        parts.append(("customers", _clamp(share["good"] + 0.5 * share["mid"]), 40))
        if risk_n:
            actions.append(T["risk"].format(n=f"{risk_n:,}"))
        if champ_n:
            actions.append(T["champ"].format(n=f"{champ_n:,}"))

    prod = r.get("products")
    if prod:
        total = sum(prod["counts"].values()) or 1
        score = 100 - 100 * prod["counts"]["Slow"] / total - min(20, 4 * len(prod["low_stock"]))
        parts.append(("products", _clamp(score), 30))
        if prod["low_stock"]:
            actions.insert(0, T["low"].format(name=prod["low_stock"][0]["name"]))
        if prod["slow"]:
            fast = prod["fast"][0]["name"] if prod["fast"] else None
            key = "slow" if fast else "slow_alone"
            actions.append(T[key].format(name=prod["slow"][0]["name"], fast=fast))

    dem = r.get("demand")
    if dem:
        recent = dem["month_units"][-3:]
        if dem.get("forecast_units") is not None and recent and np.mean(recent) > 0:
            ratio = dem["forecast_units"] / float(np.mean(recent))
            parts.append(("demand", _clamp(70 + (ratio - 1) * 150), 30))
        if dem.get("best_months"):
            months = ", ".join(MONTHS_TA.get(m, m) if lang == "ta" else m for m in dem["best_months"])
            actions.append(T["peak"].format(months=months))

    if not parts:
        return None
    weight = sum(w for _, _, w in parts)
    score = int(round(sum(s * w for _, s, w in parts) / weight))
    good, okay, bad = T["labels"]
    return {
        "score": score,
        "label": good if score >= 75 else okay if score >= 50 else bad,
        "tone": "good" if score >= 75 else "okay" if score >= 50 else "bad",
        "parts": [{"name": T["parts"][k], "score": int(round(s))} for k, s, _ in parts],
        "actions": actions[:5],
    }
