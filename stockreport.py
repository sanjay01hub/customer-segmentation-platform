"""Option 3: stock report for a shop.

Works with two kinds of files:
  A) a stock list: one row per product with a stock column (price, reorder level
     and units sold are optional);
  B) sales rows with a date and a stock column (sales speed is worked out for you).
"""
import math
import re
import numpy as np
import pandas as pd

from datareport import load_any, fmt, _key

ALIASES = {
    "product": ["product", "productname", "item", "itemname", "description", "name", "sku",
                "productcode", "itemcode", "stockcode", "particulars"],
    "stock": ["stock", "stockinhand", "instock", "onhand", "inventory", "quantityinstock", "stockleft",
              "currentstock", "qtyinstock", "available", "balance", "closingstock", "stockquantity"],
    "price": ["price", "unitprice", "sellingprice", "mrp", "rate", "costprice", "purchaseprice", "itemprice"],
    "reorder": ["reorderlevel", "reorderpoint", "minstock", "minimumstock", "minqty", "safetystock", "reorder"],
    "sold": ["sold", "unitssold", "quantitysold", "qtysold", "monthlysales", "salesqty"],
    "qty": ["quantity", "qty", "units"],
    "date": ["date", "invoicedate", "orderdate", "saledate", "transactiondate", "purchasedate"],
}

TXT = {
    "mode_list": ("Your file is a stock list. Out-of-stock and low-stock are judged from your reorder level, or compared with your other products.",
                  "உங்கள் கோப்பு இருப்புப் பட்டியல். இருப்பு தீர்ந்தது / குறைவு என்பது உங்கள் மறுஆர்டர் நிலை அல்லது மற்ற பொருட்களுடன் ஒப்பிட்டு முடிவு செய்யப்படுகிறது."),
    "mode_rel": ("Your file has no reorder level or sales speed, so low and high stock are compared with your other products. Add a reorder level column for exact alerts.",
                 "உங்கள் கோப்பில் மறுஆர்டர் நிலை அல்லது விற்பனை வேகம் இல்லை, எனவே குறைவு / அதிகம் என்பது மற்ற பொருட்களுடன் ஒப்பிடப்படுகிறது. துல்லியமான எச்சரிக்கைக்கு மறுஆர்டர் நிலை நெடுவரிசையைச் சேர்க்கவும்."),
    "mode_sales": ("Sales speed was worked out from your sales rows, so \"days of cover\" shows how long the stock will last.",
                   "உங்கள் விற்பனை வரிசைகளிலிருந்து விற்பனை வேகம் கணக்கிடப்பட்டது, எனவே \"எத்தனை நாளுக்கு இருப்பு\" எவ்வளவு காலம் போதும் என்பதைக் காட்டும்."),
    "mode_sold": ("Your file has units sold per product, so \"days of cover\" assumes that is one month of sales.",
                  "உங்கள் கோப்பில் ஒவ்வொரு பொருளுக்கும் விற்ற அலகுகள் உள்ளன, எனவே \"எத்தனை நாளுக்கு இருப்பு\" அதை ஒரு மாத விற்பனையாகக் கருதுகிறது."),
    "tip_out": ("Reorder these first. Customers who find them missing may go to another shop.",
                "இவற்றை முதலில் மறுஆர்டர் செய்யுங்கள். இவை இல்லையென்றால் வாடிக்கையாளர்கள் வேறு கடைக்குச் செல்லலாம்."),
    "tip_reorder": ("Order these soon. Stock will run out before the next delivery.",
                    "இவற்றை விரைவில் ஆர்டர் செய்யுங்கள். அடுத்த விநியோகத்துக்கு முன் இருப்பு தீர்ந்துவிடும்."),
    "tip_over": ("Too much stock. Do not reorder; run an offer or a bundle to free the money.",
                 "இருப்பு அதிகம். மீண்டும் ஆர்டர் செய்ய வேண்டாம்; சலுகை அல்லது தொகுப்பு விற்பனை மூலம் பணத்தை விடுவிக்கவும்."),
    "tip_dead": ("These have stock but no sales. Put them on offer or return them to the supplier.",
                 "இவற்றுக்கு இருப்பு உள்ளது ஆனால் விற்பனை இல்லை. சலுகை கொடுங்கள் அல்லது விநியோகஸ்தருக்குத் திருப்பி அனுப்புங்கள்."),
    "no_cols": ("A stock report needs a product name column and a stock column (for example Product and Stock).",
                "இருப்பு அறிக்கைக்கு பொருள் பெயர் நெடுவரிசையும் இருப்பு நெடுவரிசையும் தேவை (எ.கா. Product, Stock)."),
    "value": ("About {v} is tied up in stock.", "இருப்பில் சுமார் {v} முடங்கியுள்ளது."),
    "value_over": ("{v} of that is in overstocked or non-selling items.",
                   "அதில் {v} அதிக இருப்பு அல்லது விற்பனையாகாத பொருட்களில் உள்ளது."),
    "a_out": ("Reorder {n} out-of-stock product(s) today.", "இருப்பு தீர்ந்த {n} பொருட்களை இன்றே மறுஆர்டர் செய்யுங்கள்."),
    "a_reorder": ("Place orders for {n} product(s) that are about to run out.", "தீரப்போகும் {n} பொருட்களுக்கு ஆர்டர் கொடுங்கள்."),
    "a_over": ("Stop buying {n} overstocked product(s) and run an offer.", "அதிக இருப்புள்ள {n} பொருட்களை வாங்குவதை நிறுத்தி சலுகை நடத்துங்கள்."),
    "a_dead": ("Clear {n} product(s) that are not selling at all.", "விற்பனையே ஆகாத {n} பொருட்களை விற்றுத் தீருங்கள்."),
    "a_ok": ("Your stock looks balanced. Check it once a week.", "உங்கள் இருப்பு சமநிலையில் உள்ளது. வாரம் ஒருமுறை சரிபாருங்கள்."),
}


def t(key, lang, **kw):
    en, ta = TXT[key]
    return (ta if lang == "ta" else en).format(**kw)


def _find(df, names, used):
    by_key = {_key(c): c for c in df.columns}
    for n in names:
        if n in by_key and by_key[n] not in used:
            used.add(by_key[n])
            return by_key[n]
    return None


def _num(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[,\s₹$€£]", "", regex=True), errors="coerce")


def build_stock(path, lang="en"):
    df, truncated = load_any(path)
    used = set()
    pcol = _find(df, ALIASES["product"], used)
    scol = _find(df, ALIASES["stock"], used)
    dcol = _find(df, ALIASES["date"], used)
    qcol = _find(df, ALIASES["qty"], used)
    # a plain Quantity column is the stock only when the file has no dates (a stock list)
    if scol is None and qcol is not None and dcol is None:
        scol, qcol = qcol, None
    price = _find(df, ALIASES["price"], used)
    rcol = _find(df, ALIASES["reorder"], used)
    sold = _find(df, ALIASES["sold"], used)
    if pcol is None or scol is None:
        raise ValueError(t("no_cols", lang))

    df[scol] = _num(df[scol])
    if price:
        df[price] = _num(df[price])
    if rcol:
        df[rcol] = _num(df[rcol])
    if sold:
        df[sold] = _num(df[sold])
    df[pcol] = df[pcol].astype(str).str.strip()
    df = df.dropna(subset=[scol])
    if df.empty:
        raise ValueError(t("no_cols", lang))

    rate = None  # units per day
    sales_mode = dcol is not None and (qcol or sold) is not None
    if sales_mode:
        df[dcol] = pd.to_datetime(df[dcol], errors="coerce", format="mixed")
        df = df.dropna(subset=[dcol])
        qc = qcol or sold
        df[qc] = _num(df[qc])
        span = max((df[dcol].max() - df[dcol].min()).days, 1)
        g = df.sort_values(dcol).groupby(pcol)
        p = pd.DataFrame({"stock": g[scol].last(), "units": g[qc].sum()})
        p["rate"] = p["units"] / span
        if price:
            p["price"] = g[price].last()
        if rcol:
            p["reorder"] = g[rcol].last()
        mode = "sales"
    else:
        g = df.groupby(pcol)
        p = pd.DataFrame({"stock": g[scol].sum()})
        if price:
            p["price"] = g[price].last()
        if rcol:
            p["reorder"] = g[rcol].last()
        if sold:
            p["rate"] = g[sold].sum() / 30.0
            mode = "sold"
        else:
            mode = "list" if rcol else "relative"

    has_rate = "rate" in p
    p["cover"] = np.where(p["rate"] > 0, p["stock"] / p["rate"], np.nan) if has_rate else np.nan
    q20 = p["stock"].quantile(0.2)
    q90 = p["stock"].quantile(0.9)

    def status(r):
        s = r["stock"]
        if s <= 0:
            return "Out of stock"
        if has_rate and r["rate"] == 0:
            return "No sales"
        if "reorder" in r and pd.notna(r.get("reorder")) and s <= r["reorder"]:
            return "Reorder now"
        if has_rate and pd.notna(r["cover"]):
            if r["cover"] < 7:
                return "Reorder now"
            if r["cover"] < 14:
                return "Low"
            if r["cover"] > 90:
                return "Overstocked"
            return "OK"
        if not has_rate and "reorder" not in p:
            if s <= q20 and q20 < q90:
                return "Low"
            if s >= q90 and q20 < q90:
                return "Overstocked"
        return "OK"

    p["status"] = p.apply(status, axis=1)

    def order_qty(r):
        if r["status"] not in ("Out of stock", "Reorder now", "Low"):
            return None
        if has_rate and r["rate"] > 0:
            return int(max(0, math.ceil(r["rate"] * 30 - r["stock"])))
        if "reorder" in r and pd.notna(r.get("reorder")):
            return int(max(0, math.ceil(r["reorder"] * 2 - r["stock"])))
        return None

    p["order"] = p.apply(order_qty, axis=1)
    if "price" in p:
        p["value"] = p["stock"].clip(lower=0) * p["price"]

    def rows(name, limit=15):
        sub = p[p["status"] == name]
        if name in ("Reorder now", "Low") and has_rate:
            sub = sub.sort_values("cover")
        elif name == "Overstocked" or name == "No sales":
            sub = sub.sort_values("value" if "value" in sub else "stock", ascending=False)
        out = []
        for n, r in sub.head(limit).iterrows():
            out.append({
                "name": n, "stock": fmt(r["stock"]),
                "cover": None if pd.isna(r["cover"]) else fmt(r["cover"]),
                "order": int(r["order"]) if pd.notna(r["order"]) else None,
                "value": fmt(r["value"]) if "value" in r and pd.notna(r.get("value")) else None,
            })
        return {"count": int((p["status"] == name).sum()), "rows": out}

    sections = {k: rows(k) for k in ("Out of stock", "Reorder now", "Low", "Overstocked", "No sales")}
    counts = {k: int((p["status"] == k).sum()) for k in ("Out of stock", "Reorder now", "Low", "OK", "Overstocked", "No sales")}

    findings, actions = [], []
    key = {"list": "mode_list", "relative": "mode_rel", "sales": "mode_sales", "sold": "mode_sold"}[mode]
    findings.append(("info", t(key, lang)))
    total_value = over_value = None
    if "value" in p:
        total_value = float(p["value"].sum())
        over_value = float(p.loc[p["status"].isin(["Overstocked", "No sales"]), "value"].sum())
        findings.append(("info", t("value", lang, v=fmt(total_value))))
        if over_value > 0:
            findings.append(("warn", t("value_over", lang, v=fmt(over_value))))
    if counts["Out of stock"]:
        actions.append(t("a_out", lang, n=counts["Out of stock"]))
    if counts["Reorder now"] + counts["Low"]:
        actions.append(t("a_reorder", lang, n=counts["Reorder now"] + counts["Low"]))
    if counts["Overstocked"]:
        actions.append(t("a_over", lang, n=counts["Overstocked"]))
    if counts["No sales"]:
        actions.append(t("a_dead", lang, n=counts["No sales"]))
    if not actions:
        actions.append(t("a_ok", lang))

    top_stock = []
    if "value" in p:
        tv = p.sort_values("value", ascending=False).head(8)
        mx = float(tv["value"].max()) or 1
        top_stock = [{"label": n, "value": fmt(r["value"]), "pct": round(float(r["value"]) / mx * 100, 1)}
                     for n, r in tv.iterrows()]

    tips = {"Out of stock": t("tip_out", lang), "Reorder now": t("tip_reorder", lang),
            "Low": t("tip_reorder", lang), "Overstocked": t("tip_over", lang), "No sales": t("tip_dead", lang)}
    return {"products": int(len(p)), "mode": mode, "counts": counts, "sections": sections,
            "findings": [{"tone": a, "text": b} for a, b in findings], "actions": actions,
            "has_rate": has_rate, "has_value": "value" in p, "top_stock": top_stock, "tips": tips,
            "total_value": None if total_value is None else fmt(total_value)}
