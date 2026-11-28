"""Option 1: report for ANY csv / xlsx file.

The file can be about anything (sales, marks, patients, attendance...).
We read every column, work out what kind of data it holds, and write a
plain-language report with findings and things to do next.
"""
import re
import numpy as np
import pandas as pd

MAX_ROWS = 150000
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

MEASURE_WORDS = ("amount", "total", "sales", "revenue", "profit", "income", "turnover", "payment",
                 "bill", "spend", "marks", "score", "salary", "fee", "cost", "price", "value",
                 "quantity", "qty", "units", "rating", "age")
ADD_WORDS = ("amount", "total", "sales", "revenue", "profit", "income", "turnover", "payment", "bill",
             "spend", "quantity", "qty", "units", "expense", "fee")
ID_ENDINGS = ("id", "no", "number", "code", "sku", "phone", "mobile", "pin", "zip", "serial", "roll", "sno", "slno",
              "invoice")


# --------------------------------------------------------------- text (English / Tamil)
TXT = {
    "read": ("{rows} rows and {cols} columns were read from your file.",
             "உங்கள் கோப்பிலிருந்து {rows} வரிசைகளும் {cols} நெடுவரிசைகளும் படிக்கப்பட்டன."),
    "no_missing": ("No values are missing. Your data is complete.",
                   "எந்த மதிப்பும் விடுபடவில்லை. உங்கள் தரவு முழுமையாக உள்ளது."),
    "missing": ("{col} is empty in {pct}% of rows. Fill it in, or it will weaken any result that uses it.",
                "{col} நெடுவரிசை {pct}% வரிசைகளில் காலியாக உள்ளது. அதை நிரப்புங்கள்; இல்லையெனில் முடிவுகள் பலவீனமாகும்."),
    "dups": ("{n} rows are exact duplicates. Remove them so nothing is counted twice.",
             "{n} வரிசைகள் அப்படியே நகல்கள். எதுவும் இரண்டு முறை கணக்கிடப்படாமல் இருக்க அவற்றை நீக்குங்கள்."),
    "no_dups": ("There are no duplicate rows.", "நகல் வரிசைகள் எதுவும் இல்லை."),
    "measure": ("Main number to study: {col}. Total {total}, average {avg}, highest {mx}.",
                "ஆய்வுக்கான முக்கிய எண்: {col}. மொத்தம் {total}, சராசரி {avg}, அதிகபட்சம் {mx}."),
    "best_sum": ("In {col}, \"{top}\" brings the most {m} ({share}% of the total). \"{low}\" brings the least.",
                 "{col} பிரிவில் \"{top}\" அதிக {m} தருகிறது (மொத்தத்தில் {share}%). \"{low}\" குறைவாகத் தருகிறது."),
    "best_mean": ("In {col}, \"{top}\" has the highest average {m}. \"{low}\" has the lowest.",
                  "{col} பிரிவில் \"{top}\" அதிக சராசரி {m} கொண்டுள்ளது. \"{low}\" குறைவாகக் கொண்டுள்ளது."),
    "top_count": ("In {col}, \"{top}\" is the most common ({share}% of rows).",
                  "{col} பிரிவில் \"{top}\" அதிகமாக வருகிறது (வரிசைகளில் {share}%)."),
    "concentrated": ("{share}% of {m} depends on just one {col} value (\"{top}\"). That is risky if it drops.",
                     "{m}-இல் {share}% ஒரே {col} மதிப்பைச் (\"{top}\") சார்ந்துள்ளது. அது குறைந்தால் ஆபத்து."),
    "outliers": ("{col} has {n} unusual value(s) (highest {mx}). Check if they are mistakes or real big cases.",
                 "{col}-இல் {n} வழக்கத்துக்கு மாறான மதிப்பு(கள்) உள்ளன (அதிகபட்சம் {mx}). அவை தவறா அல்லது உண்மையான பெரிய நிகழ்வுகளா எனச் சரிபாருங்கள்."),
    "corr": ("{a} and {b} move together (relationship {r}). A change in one usually comes with a change in the other.",
             "{a} மற்றும் {b} ஒன்றாக மாறுகின்றன (தொடர்பு {r}). ஒன்று மாறினால் மற்றொன்றும் மாறும்."),
    "corr_neg": ("{a} and {b} move in opposite directions (relationship {r}).",
                 "{a} மற்றும் {b} எதிர் திசையில் மாறுகின்றன (தொடர்பு {r})."),
    "trend_up": ("{m} is rising: the latest period ({last}) is {pct}% above the recent average.",
                 "{m} உயர்ந்து வருகிறது: சமீபத்திய காலம் ({last}) சமீபத்திய சராசரியை விட {pct}% அதிகம்."),
    "trend_down": ("{m} is falling: the latest period ({last}) is {pct}% below the recent average.",
                   "{m} குறைந்து வருகிறது: சமீபத்திய காலம் ({last}) சமீபத்திய சராசரியை விட {pct}% குறைவு."),
    "trend_flat": ("{m} is steady over the recent periods.",
                   "சமீபத்திய காலங்களில் {m} நிலையாக உள்ளது."),
    "best_day": ("{day} is your strongest day of the week.", "வாரத்தில் {day} உங்கள் சிறந்த நாள்."),
    "dates": ("Dates run from {a} to {b}.", "தேதிகள் {a} முதல் {b} வரை உள்ளன."),
    "rows_per": ("Rows per period", "காலம் வாரியான வரிசைகள்"),
    "by_sum": ("{m} (total) by {c}", "{c} வாரியாக {m} (மொத்தம்)"),
    "by_mean": ("{m} (average) by {c}", "{c} வாரியாக {m} (சராசரி)"),
    "no_measure": ("No number column was found, so the report counts rows instead.",
                   "எண் நெடுவரிசை எதுவும் இல்லை, எனவே வரிசைகளை எண்ணி அறிக்கை தயாரிக்கப்பட்டது."),
    "truncated": ("Your file is large, so only the first {n} rows were used.",
                  "உங்கள் கோப்பு பெரியது, எனவே முதல் {n} வரிசைகள் மட்டுமே பயன்படுத்தப்பட்டன."),
    "best_period": ("{p} has the highest {m} ({v}).", "{p} மாதத்தில் {m} அதிகம் ({v})."),
    "forecast": ("Rough forecast: next period {m} is likely to be about {v} if the recent trend continues.",
                 "தோராய முன்கணிப்பு: சமீபத்திய போக்கு தொடர்ந்தால் அடுத்த காலத்தில் {m} சுமார் {v} இருக்கும்."),
    "g_up": ("{g} ({c}): {m} is rising from {a} to {b}.", "{g} ({c}): {m} {a}-இலிருந்து {b} ஆக உயர்கிறது."),
    "g_down": ("{g} ({c}): {m} is falling from {a} to {b}.", "{g} ({c}): {m} {a}-இலிருந்து {b} ஆகக் குறைகிறது."),
    "g_dip": ("{g} ({c}) dropped {pct}% in {p} compared with the period before.", "{g} ({c}) {p} காலத்தில் முந்தைய காலத்தை விட {pct}% குறைந்தது."),
    "g_fc": ("Rough forecast for the next period: {items}.", "அடுத்த காலத்திற்கான தோராய முன்கணிப்பு: {items}."),
    "a_grow": ("Plan more stock and effort for \"{g}\" ({c}); its {m} is rising.", "\"{g}\" ({c})-க்கு அதிக இருப்பும் முயற்சியும் திட்டமிடுங்கள்; அதன் {m} உயர்கிறது."),
    "a_fall": ("Find out why \"{g}\" ({c}) is falling (price, stock, competition) and act on it.", "\"{g}\" ({c}) ஏன் குறைகிறது (விலை, இருப்பு, போட்டி) எனக் கண்டறிந்து நடவடிக்கை எடுங்கள்."),
    # actions
    "a_missing": ("Fill the empty cells in {cols}.", "{cols} நெடுவரிசைகளில் உள்ள காலிக் கட்டங்களை நிரப்புங்கள்."),
    "a_dups": ("Remove the duplicate rows.", "நகல் வரிசைகளை நீக்குங்கள்."),
    "a_top": ("Protect and grow what works: look at why \"{top}\" does well in {col} and repeat it.",
              "நன்றாக நடப்பதைப் பாதுகாத்து வளர்க்கவும்: {col} பிரிவில் \"{top}\" ஏன் சிறப்பாக உள்ளது என்று பார்த்து அதை மீண்டும் செய்யுங்கள்."),
    "a_low": ("Find out why \"{low}\" in {col} is lowest. Fix it, or spend less effort on it.",
              "{col} பிரிவில் \"{low}\" ஏன் குறைவாக உள்ளது எனக் கண்டறியுங்கள். சரிசெய்யுங்கள் அல்லது அதில் முயற்சியைக் குறைக்கவும்."),
    "a_down": ("The latest trend is down. Look at what changed recently and act this week.",
               "சமீபத்திய போக்கு குறைகிறது. சமீபத்தில் என்ன மாறியது எனப் பார்த்து இந்த வாரமே நடவடிக்கை எடுங்கள்."),
    "a_up": ("The trend is up. Keep what you are doing and make sure you can handle more demand.",
             "போக்கு உயர்கிறது. இப்போது செய்வதைத் தொடருங்கள்; அதிகத் தேவையைச் சமாளிக்க தயாராக இருங்கள்."),
    "a_day": ("Plan your offers and staff around {day}, your strongest day.",
              "உங்கள் சிறந்த நாளான {day}-ஐ மையமாக வைத்து சலுகைகளையும் ஆட்களையும் திட்டமிடுங்கள்."),
    "a_outliers": ("Check the unusual values in {cols} before trusting the averages.",
                   "சராசரிகளை நம்பும் முன் {cols}-இல் உள்ள வழக்கத்துக்கு மாறான மதிப்புகளைச் சரிபாருங்கள்."),
    "a_more": ("Add a date column and a customer or product column to unlock trends and deeper findings.",
               "போக்குகளையும் ஆழமான முடிவுகளையும் பெற தேதி மற்றும் வாடிக்கையாளர் அல்லது பொருள் நெடுவரிசையைச் சேர்க்கவும்."),
}


def t(key, lang, **kw):
    en, ta = TXT[key]
    return (ta if lang == "ta" else en).format(**kw)


def fmt(x):
    x = float(x)
    if abs(x) >= 100:
        return f"{x:,.0f}"
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def _key(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


# --------------------------------------------------------------- loading
SUPPORTED = ("csv", "tsv", "txt", "xlsx", "xlsm", "xls", "ods", "json", "jsonl", "pdf")


def _fix_header(df):
    """Some files have title rows above the real column names. Find the real header row."""
    if len(df) < 3:
        return df
    unnamed = sum(str(c).startswith("Unnamed") for c in df.columns)
    if unnamed < max(1, len(df.columns) // 2):
        return df
    for i in range(min(8, len(df))):
        row = df.iloc[i]
        if row.notna().mean() >= 0.8 and all(isinstance(x, str) for x in row.dropna()):
            out = df.iloc[i + 1:].copy()
            out.columns = [str(x) for x in row.fillna("")]
            return out.reset_index(drop=True)
    return df


def _read_text_table(path):
    last = None
    for enc in ("utf-8-sig", "utf-16", "ISO-8859-1"):
        try:
            best = None
            for sep in (",", "\t", ";", "|"):
                try:
                    d = pd.read_csv(path, nrows=MAX_ROWS + 1, encoding=enc, sep=sep, engine="python")
                except UnicodeError:
                    raise
                except Exception:
                    continue
                if best is None or len(d.columns) > len(best.columns):
                    best = d
            if best is not None and len(best.columns) >= 2:
                return best
            return pd.read_csv(path, nrows=MAX_ROWS + 1, encoding=enc, sep=None, engine="python")
        except UnicodeError as e:
            last = e
        except Exception as e:
            last = e
            break
    raise ValueError("The text file could not be read as a table. Save it as CSV or XLSX.") from last


def _read_pdf(path):
    try:
        import pdfplumber
    except ImportError:
        raise ValueError("PDF reading is not switched on on this server. Please save the table as CSV or XLSX.")
    frames = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:60]:
            for tb in page.extract_tables():
                if not tb or len(tb) < 2:
                    continue
                head = [str(h or "").strip() for h in tb[0]]
                if frames and len(head) == len(frames[0].columns) and head != list(frames[0].columns):
                    frames.append(pd.DataFrame(tb, columns=list(frames[0].columns)))   # continued table
                else:
                    frames.append(pd.DataFrame(tb[1:], columns=head))
    if not frames:
        raise ValueError("No table was found in this PDF (a scanned PDF cannot be read). Please upload CSV or XLSX.")
    cols = list(frames[0].columns)
    same = [f for f in frames if list(f.columns) == cols]
    return pd.concat(same or frames[:1], ignore_index=True)


def load_any(path):
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in ("xlsx", "xlsm", "xls", "ods"):
        engine = {"xls": "xlrd", "ods": "odf"}.get(ext)
        try:
            book = pd.read_excel(path, sheet_name=None, nrows=MAX_ROWS + 1, engine=engine)
        except ImportError:
            raise ValueError(f".{ext} files need an extra package on this server. Please save the file as .xlsx or .csv.")
        sheets = [(n, d) for n, d in book.items() if not d.dropna(how="all").empty]
        if not sheets:
            raise ValueError("The file is empty.")
        df = max(sheets, key=lambda x: x[1].size)[1]          # use the biggest sheet
    elif ext == "json":
        import json
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            data = max(lists, key=len) if lists else [data]
        df = pd.json_normalize(data)
    elif ext == "jsonl":
        df = pd.read_json(path, lines=True)
    elif ext == "pdf":
        df = _read_pdf(path)
    else:                                                      # csv, tsv, txt and anything else
        df = _read_text_table(path)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = _fix_header(df).dropna(how="all")
    if df.empty or len(df.columns) == 0:
        raise ValueError("The file is empty.")
    truncated = len(df) > MAX_ROWS
    df = df.iloc[:MAX_ROWS].copy()
    df.columns = [str(c).strip() or f"Column {i + 1}" for i, c in enumerate(df.columns)]
    for c in df.columns:                                       # lists / dicts from JSON -> text
        if df[c].map(lambda x: isinstance(x, (list, dict))).any():
            df[c] = df[c].astype(str)
    return df, truncated


_MN = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
       "november", "december"]


def _month_idx(v):
    x = str(v).strip().lower().rstrip(".")
    for i, m in enumerate(_MN):
        if x == m or x == m[:3] or (x == "sept" and i == 8):
            return i + 1
    return None


def _date_col(df, kinds):
    dates = [c for c in df.columns if kinds[c] == "date"]
    return next((c for c in dates if "date" in _key(c)), dates[0]) if dates else None


def _period_keys(df, kinds):
    """Return (keys, label_fn) giving every row a sortable period (month / week), or None."""
    dc = _date_col(df, kinds)
    if dc:
        d = df[dc]
        if d.notna().sum() < 5:
            return None
        span = (d.max() - d.min()).days
        if span < 14:
            return None
        freq = "M" if span >= 75 else "W"
        keys = d.dt.to_period(freq)
        return keys, (lambda p: str(p.start_time.date()) if freq == "W" else str(p))
    mc = next((c for c in df.columns if kinds[c] == "month"), None)
    if mc:
        return df[mc].map(_month_idx), (lambda k: _MN[int(k) - 1].capitalize())
    return None


def _forecast(vals, minimum=3):
    v = np.array(list(vals)[-6:], dtype=float)
    if len(v) < minimum or np.allclose(v, v[0]):
        return None
    a, b = np.polyfit(np.arange(len(v)), v, 1)
    f = a * len(v) + b
    if (v >= 0).all():
        f = max(f, 0)
    return float(f)


def _id_name(name):
    k = _key(name)
    return any(k.endswith(e) for e in ID_ENDINGS)


def _prepare(df):
    """Work out the kind of every column; convert text numbers and dates."""
    kinds = {}
    n = len(df)
    for c in list(df.columns):
        s = df[c]
        nn = s.dropna()
        if nn.empty:
            kinds[c] = "empty"
            continue
        if pd.api.types.is_bool_dtype(s):
            df[c] = s.astype(str)
            kinds[c] = "category"
            continue
        if pd.api.types.is_datetime64_any_dtype(s):
            kinds[c] = "date"
            continue
        if pd.api.types.is_numeric_dtype(s):
            ratio = nn.nunique() / max(len(nn), 1)
            running = (pd.api.types.is_integer_dtype(s) and n > 20 and ratio >= 0.98
                       and bool(nn.is_monotonic_increasing))
            kinds[c] = "id" if ((_id_name(c) and ratio > 0.5) or running) else "number"
            continue
        strs = nn.astype(str).str.strip()
        cleaned = strs.str.replace(r"[,\s₹$€£%]", "", regex=True)
        as_num = pd.to_numeric(cleaned, errors="coerce")
        if as_num.notna().mean() >= 0.9:
            df[c] = pd.to_numeric(s.astype(str).str.replace(r"[,\s₹$€£%]", "", regex=True), errors="coerce")
            kinds[c] = "id" if _id_name(c) else "number"
            continue
        if strs.str.contains(r"\d").mean() >= 0.9:
            sample = strs.head(300)
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            sane = parsed.dt.year.between(1950, 2100) if parsed.notna().any() else parsed.notna()
            looks = strs.head(300).str.contains(r"[-/.]\d|\d[-/.]|[A-Za-z]{3,}\s*\d{1,2}|\d{1,2}\s*[A-Za-z]{3,}|\d{4}", regex=True)
            if parsed.notna().mean() >= 0.9 and sane.mean() >= 0.9 and looks.mean() >= 0.9:
                df[c] = pd.to_datetime(s, errors="coerce", format="mixed")
                kinds[c] = "date"
                continue
        if strs.map(_month_idx).notna().mean() >= 0.9:
            kinds[c] = "month"
            continue
        uniq = nn.nunique()
        ratio = uniq / max(len(nn), 1)
        avg_len = strs.str.len().mean()
        if n > 20 and ratio > 0.9:
            kinds[c] = "text" if avg_len > 30 else "id"
        elif uniq <= max(30, 0.1 * n):
            kinds[c] = "category"
        else:
            kinds[c] = "text"
    return kinds


# --------------------------------------------------------------- profile
def _profile(df, kinds):
    rows = []
    n = len(df)
    for c in df.columns:
        s = df[c]
        kind = kinds[c]
        miss = int(s.isna().sum())
        item = {"name": c, "kind": kind, "missing": miss,
                "missing_pct": round(miss / n * 100, 1) if n else 0,
                "unique": int(s.nunique()), "detail": ""}
        if kind == "number":
            v = s.dropna()
            item["detail"] = f"min {fmt(v.min())} · avg {fmt(v.mean())} · median {fmt(v.median())} · max {fmt(v.max())}"
        elif kind == "date":
            v = s.dropna()
            item["detail"] = f"{v.min().strftime('%d %b %Y')} – {v.max().strftime('%d %b %Y')}"
        elif kind in ("category", "month"):
            top = s.value_counts().head(3)
            item["detail"] = ", ".join(f"{k} ({v})" for k, v in top.items())
        rows.append(item)
    return rows


def _bars(labels, values, limit=8):
    pairs = [(str(l), float(v)) for l, v in zip(labels, values)][:limit]
    mx = max((abs(v) for _, v in pairs), default=0) or 1
    return [{"label": l, "value": fmt(v), "pct": round(abs(v) / mx * 100, 1), "neg": v < 0} for l, v in pairs]


def _pick_measure(df, kinds):
    nums = [c for c in df.columns if kinds[c] == "number"]
    if not nums:
        return None
    for w in MEASURE_WORDS:
        for c in nums:
            if w in _key(c):
                return c
    return nums[0]


def _trend_month(df, mc, measure, lang, use_mean):
    d = df.copy()
    d["_m"] = d[mc].map(_month_idx)
    d = d.dropna(subset=["_m"])
    if measure:
        g = d.groupby("_m")[measure].mean() if use_mean else d.groupby("_m")[measure].sum()
    else:
        g = d.groupby("_m").size()
    g = g.sort_index()
    if len(g) < 2:
        return mc, [], None
    names = [_MN[int(i) - 1].capitalize() for i in g.index]
    label = measure or t("rows_per", lang)
    last_v = float(g.iloc[-1])
    prev = float(g.iloc[max(0, len(g) - 4):-1].mean())
    pct = round((last_v - prev) / abs(prev) * 100) if prev else 0
    direction = "up" if pct > 10 else "down" if pct < -10 else "flat"
    info = {"direction": direction, "pct": abs(pct), "last": names[-1], "label": label, "span": 0,
            "from": names[0], "to": names[-1], "best_day": None,
            "best": (names[int(np.argmax(g.values))], float(g.max()))}
    f = _forecast(g.values, 3)
    if f is not None:
        info["forecast"] = f
    return mc, _bars(names, g.values, limit=12), info


def _trend(df, kinds, measure, lang, use_mean=False):
    dates = [c for c in df.columns if kinds[c] == "date"]
    if not dates:
        mc = next((c for c in df.columns if kinds[c] == "month"), None)
        if mc:
            return _trend_month(df, mc, measure, lang, use_mean)
        return None, [], None
    dc = _date_col(df, kinds)
    d = df.dropna(subset=[dc]).copy()
    if len(d) < 5:
        return None, [], None
    span = (d[dc].max() - d[dc].min()).days
    freq = "M" if span >= 75 else "W" if span >= 14 else "D"
    d["_p"] = d[dc].dt.to_period(freq)
    if measure:
        g = d.groupby("_p")[measure].mean() if use_mean else d.groupby("_p")[measure].sum()
    else:
        g = d.groupby("_p").size()
    if freq == "M" and len(g) > 3:
        last = d[dc].max()
        if last.day < last.days_in_month - 2:
            g = g.iloc[:-1]
    if freq == "W" and len(g) > 3 and d[dc].max().dayofweek < 6:
        g = g.iloc[:-1]                      # the last week is not finished yet
    g = g.tail(24)
    if len(g) < 2:
        return dc, [], None
    label = measure or t("rows_per", lang)
    if freq == "D" and len(g) >= 8:
        # a single day is too noisy: compare the last 7 days with the 7 days before them
        last_v = float(g.iloc[-7:].mean())
        prev = float(g.iloc[-14:-7].mean()) if len(g) >= 10 else float(g.iloc[:-7].mean())
        last_label = f"{g.index[-7]} – {g.index[-1]}"
    else:
        last_v = float(g.iloc[-1])
        prev = float(g.iloc[max(0, len(g) - 4):-1].mean())
        last_label = str(g.index[-1].start_time.date()) if freq == "W" else str(g.index[-1])
    direction = None
    pct = 0
    if prev:
        pct = round((last_v - prev) / abs(prev) * 100)
        direction = "up" if pct > 10 else "down" if pct < -10 else "flat"
    info = {"direction": direction, "pct": abs(pct), "last": last_label, "label": label,
            "span": span, "from": d[dc].min().strftime("%d %b %Y"), "to": d[dc].max().strftime("%d %b %Y")}
    bars = _bars([str(i) for i in g.index], g.values, limit=24)
    if freq == "M" and len(g) >= 3:
        info["best"] = (str(g.index[int(np.argmax(g.values))]), float(g.max()))
    if len(g) >= 4:
        f = _forecast(g.values, 4)
        if f is not None:
            info["forecast"] = f
    best_day = None
    if span >= 14:
        by = d.groupby(d[dc].dt.dayofweek)
        wd = (by[measure].mean() if use_mean else by[measure].sum()) if measure else by.size()
        if len(wd) > 1 and wd.max() > 0:
            best_day = DAYS[int(wd.idxmax())]
    info["best_day"] = best_day
    return dc, bars, info


def _group_trends(df, kinds, measure, use_mean, pk, lang):
    keys, label = pk
    F, A = [], []
    cats = [c for c in df.columns if kinds[c] == "category" and 2 <= df[c].nunique() <= 8]
    for c in cats[:1]:
        d = pd.DataFrame({"g": df[c], "p": keys, "v": df[measure]}).dropna()
        if d.empty:
            continue
        agg = d.groupby(["g", "p"])["v"].mean() if use_mean else d.groupby(["g", "p"])["v"].sum()
        pv = agg.unstack("g").sort_index()
        if len(pv) < 3:
            continue
        fc = []
        for g in pv.columns:
            s_ = pv[g].dropna()
            if len(s_) < 3:
                continue
            first, last = float(s_.iloc[0]), float(s_.iloc[-1])
            slope = np.polyfit(np.arange(len(s_)), s_.values.astype(float), 1)[0]
            change = (last - first) / abs(first) * 100 if first else 0
            if change >= 15 and slope > 0:
                F.append(("good", t("g_up", lang, g=g, c=c, m=measure, a=fmt(first), b=fmt(last))))
                A.append(t("a_grow", lang, g=g, c=c, m=measure))
            elif change <= -15 and slope < 0:
                F.append(("warn", t("g_down", lang, g=g, c=c, m=measure, a=fmt(first), b=fmt(last))))
                A.append(t("a_fall", lang, g=g, c=c))
            worst = None
            for i in range(1, len(s_)):
                prev = float(s_.iloc[i - 1])
                if prev > 0 and s_.iloc[i] < prev * 0.85:
                    drop = round((prev - float(s_.iloc[i])) / prev * 100)
                    if worst is None or drop > worst[0]:
                        worst = (drop, label(s_.index[i]))
            if worst:
                F.append(("warn", t("g_dip", lang, g=g, c=c, pct=worst[0], p=worst[1])))
            f = _forecast(s_.values, 3)
            if f is not None:
                fc.append(f"{g} ≈ {fmt(f)}")
        if fc:
            F.append(("info", t("g_fc", lang, items=", ".join(fc[:5]))))
    return F[:8], A[:6]


def build_report(path, lang="en"):
    df, truncated = load_any(path)
    kinds = _prepare(df)
    n = len(df)
    findings, actions = [], []

    findings.append(("info", t("read", lang, rows=f"{n:,}", cols=len(df.columns))))
    if truncated:
        findings.append(("info", t("truncated", lang, n=f"{MAX_ROWS:,}")))

    profile = _profile(df, kinds)

    # --- data quality
    bad = [p for p in profile if p["missing_pct"] >= 20]
    for p in bad[:3]:
        findings.append(("warn", t("missing", lang, col=p["name"], pct=p["missing_pct"])))
    if not any(p["missing"] for p in profile):
        findings.append(("good", t("no_missing", lang)))
    if bad:
        actions.append(t("a_missing", lang, cols=", ".join(p["name"] for p in bad[:4])))
    dup = int(df.duplicated().sum())
    if dup:
        findings.append(("warn", t("dups", lang, n=f"{dup:,}")))
        actions.append(t("a_dups", lang))
    else:
        findings.append(("good", t("no_dups", lang)))
    avg_missing = float(np.mean([p["missing_pct"] for p in profile])) if profile else 0
    quality = max(0, min(100, int(round(100 - avg_missing * 1.5 - (dup / n * 100 * 2 if n else 0)))))

    # --- main number
    measure = _pick_measure(df, kinds)
    use_mean = bool(measure and not any(w in _key(measure) for w in ADD_WORDS))
    if measure:
        v = df[measure].dropna()
        findings.append(("info", t("measure", lang, col=measure, total=fmt(v.sum()),
                                   avg=fmt(v.mean()), mx=fmt(v.max()))))
    else:
        findings.append(("info", t("no_measure", lang)))

    # --- trend
    date_col, trend_bars, trend_info = _trend(df, kinds, measure, lang, use_mean)
    if trend_info:
        findings.append(("info", t("dates", lang, a=trend_info["from"], b=trend_info["to"])))
        m = trend_info["label"]
        if trend_info["direction"] == "up":
            findings.append(("good", t("trend_up", lang, m=m, last=trend_info["last"], pct=trend_info["pct"])))
            actions.append(t("a_up", lang))
        elif trend_info["direction"] == "down":
            findings.append(("warn", t("trend_down", lang, m=m, last=trend_info["last"], pct=trend_info["pct"])))
            actions.append(t("a_down", lang))
        elif trend_info["direction"] == "flat":
            findings.append(("info", t("trend_flat", lang, m=m)))
        if trend_info.get("best"):
            findings.append(("info", t("best_period", lang, p=trend_info["best"][0], m=trend_info["label"], v=fmt(trend_info["best"][1]))))
        if trend_info.get("forecast") is not None:
            findings.append(("info", t("forecast", lang, m=trend_info["label"], v=fmt(trend_info["forecast"]))))
        if trend_info["best_day"]:
            from translate import DAYS_TA
            day = DAYS_TA.get(trend_info["best_day"], trend_info["best_day"]) if lang == "ta" else trend_info["best_day"]
            findings.append(("info", t("best_day", lang, day=day)))
            actions.append(t("a_day", lang, day=day))

    # --- by category
    cats = [c for c in df.columns if kinds[c] == "category" and 2 <= df[c].nunique() <= 30][:3]
    measure_by = []
    counts = []
    for c in cats:
        if measure:
            g = df.groupby(c)[measure].mean() if use_mean else df.groupby(c)[measure].sum()
            g = g.dropna().sort_values(ascending=False)
            if len(g) < 2:
                continue
            measure_by.append({"col": c, "title": t("by_mean" if use_mean else "by_sum", lang, m=measure, c=c),
                               "bars": _bars(g.index, g.values)})
            top, low = str(g.index[0]), str(g.index[-1])
            if use_mean:
                findings.append(("info", t("best_mean", lang, col=c, top=top, low=low, m=measure)))
            else:
                total = float(g.sum())
                share = round(float(g.iloc[0]) / total * 100) if total else 0
                findings.append(("info", t("best_sum", lang, col=c, top=top, low=low, m=measure, share=share)))
                if share >= 50 and len(g) >= 3:
                    findings.append(("warn", t("concentrated", lang, share=share, m=measure, col=c, top=top)))
            actions.append(t("a_top", lang, top=top, col=c))
            actions.append(t("a_low", lang, low=low, col=c))
        else:
            vc = df[c].value_counts()
            counts.append({"col": c, "title": f"{c}", "bars": _bars(vc.index, vc.values)})
            findings.append(("info", t("top_count", lang, col=c, top=str(vc.index[0]),
                                       share=round(float(vc.iloc[0]) / n * 100))))

    # --- each category over time (is Laptop rising? did Mobile drop?)
    pk = _period_keys(df, kinds)
    if measure and pk is not None:
        try:
            gf, ga = _group_trends(df, kinds, measure, use_mean, pk, lang)
            findings.extend(gf)
            actions.extend(ga)
        except Exception:
            pass

    # --- unusual values + relationships
    nums = [c for c in df.columns if kinds[c] == "number"]
    odd = []
    for c in nums[:8]:
        v = df[c].dropna()
        if len(v) < 20:
            continue
        q1, q3 = v.quantile(0.25), v.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        k = int(((v < q1 - 3 * iqr) | (v > q3 + 3 * iqr)).sum())
        if k:
            odd.append(c)
            findings.append(("warn", t("outliers", lang, col=c, n=k, mx=fmt(v.max()))))
    if odd:
        actions.append(t("a_outliers", lang, cols=", ".join(odd[:3])))
    if len(nums) >= 2:
        cm = df[nums[:12]].corr()
        pairs = []
        for i, a in enumerate(cm.columns):
            for b in cm.columns[i + 1:]:
                r = cm.loc[a, b]
                if pd.notna(r) and abs(r) >= 0.6:
                    pairs.append((abs(r), a, b, r))
        for _, a, b, r in sorted(pairs, reverse=True)[:2]:
            findings.append(("info", t("corr" if r > 0 else "corr_neg", lang, a=a, b=b, r=round(float(r), 2))))

    # --- histograms
    hists = []
    for c in [c for c in nums if df[c].nunique() > 5][:3]:
        v = df[c].dropna()
        cnt, edges = np.histogram(v, bins=8)
        labels = [f"{fmt(edges[i])}–{fmt(edges[i + 1])}" for i in range(len(cnt))]
        hists.append({"col": c, "bars": _bars(labels, cnt, limit=8)})

    if not date_col or not cats:
        actions.append(t("a_more", lang))

    # --- industry-specific findings (school, factory, company, clinic...)
    industry = None
    try:
        from industry import analyse_industry
        industry = analyse_industry(df, kinds, lang)
    except Exception:
        industry = None
    if industry:
        actions = industry["actions"] + actions

    return {
        "rows": n, "cols": len(df.columns), "quality": quality,
        "tone": "good" if quality >= 85 else "okay" if quality >= 60 else "bad",
        "columns": profile, "findings": [{"tone": a, "text": b} for a, b in findings],
        "actions": list(dict.fromkeys(actions))[:10], "industry": industry,
        "measure": measure, "measure_by": measure_by, "counts": counts,
        "trend": {"bars": trend_bars, "label": (trend_info or {}).get("label", "")} if trend_bars else None,
        "hists": hists,
        "preview_cols": list(df.columns[:8]),
        "preview": [[("" if pd.isna(x) else str(x)[:40]) for x in row] for row in df[list(df.columns[:8])].head(5).values.tolist()],
    }
