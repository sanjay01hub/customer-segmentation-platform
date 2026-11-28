"""Industry-aware findings on top of the general report.

We look at the column names and decide what kind of data this is
(school / college, factory, company staff, clinic, accounts, delivery).
Then we add findings, tables and actions that make sense for that business.
Nothing here is required: if the type is not clear, the general report is shown alone.
"""
import numpy as np
import pandas as pd
from datareport import _key, fmt

WORDS = {
    "education": ("mark", "score", "grade", "student", "roll", "class", "section", "subject", "exam", "cgpa", "gpa",
                  "semester", "tamil", "english", "math", "science", "social", "physics", "chemistry", "biology",
                  "computer", "hindi", "attend", "rank", "result"),
    "manufacturing": ("production", "produced", "output", "defect", "reject", "scrap", "downtime", "machine", "shift",
                      "batch", "plant", "yield", "rework", "operator", "workorder", "cycle"),
    "company": ("employee", "emp", "salary", "ctc", "department", "designation", "project", "billable", "ticket",
                "bug", "sprint", "attrition", "joining", "experience", "manager", "team", "payroll"),
    "healthcare": ("patient", "diagnosis", "doctor", "treatment", "disease", "ward", "medicine", "symptom"),
    "finance": ("expense", "income", "debit", "credit", "balance", "ledger", "transaction", "budget", "payee"),
    "logistics": ("shipment", "delivery", "route", "vehicle", "driver", "distance", "dispatch", "delay", "freight", "trip"),
}
LABEL = {
    "education": ("School / college data", "பள்ளி / கல்லூரி தரவு"),
    "manufacturing": ("Factory / manufacturing data", "தொழிற்சாலை / உற்பத்தி தரவு"),
    "company": ("Company / staff data", "நிறுவனம் / பணியாளர் தரவு"),
    "healthcare": ("Clinic / hospital data", "கிளினிக் / மருத்துவமனை தரவு"),
    "finance": ("Accounts / expense data", "கணக்கு / செலவு தரவு"),
    "logistics": ("Delivery / transport data", "விநியோகம் / போக்குவரத்து தரவு"),
}
H = {  # table headings
    "name": ("Name", "பெயர்"), "avg": ("Average", "சராசரி"), "failed": ("Failed subjects", "தோல்வி பாடங்கள்"),
    "subject": ("Subject", "பாடம்"), "pass": ("Pass %", "தேர்ச்சி %"), "high": ("Highest", "அதிகம்"),
    "low": ("Lowest", "குறைவு"), "output": ("Output", "உற்பத்தி"), "defects": ("Defects", "குறைபாடுகள்"),
    "rate": ("Defect %", "குறைபாடு %"), "down": ("Downtime", "செயலிழப்பு நேரம்"),
    "people": ("People", "நபர்கள்"), "pay": ("Average pay", "சராசரி ஊதியம்"), "late": ("Late %", "தாமதம் %"),
    "trips": ("Deliveries", "விநியோகங்கள்"),
}
TX = {
    "label": ("Detected type of data: {x}. The findings below are written for this kind of business.",
              "கண்டறியப்பட்ட தரவு வகை: {x}. கீழுள்ள முடிவுகள் இந்த வகை தொழிலுக்காக எழுதப்பட்டவை."),
    # education
    "e_subject": ("Strongest subject: {best} (average {a}). Weakest subject: {worst} (average {b}, {p}% pass).",
                  "வலுவான பாடம்: {best} (சராசரி {a}). பலவீனமான பாடம்: {worst} (சராசரி {b}, {p}% தேர்ச்சி)."),
    "e_pass": ("{p}% of students passed every subject (pass mark taken as 35). {n} students failed at least one subject.",
               "{p}% மாணவர்கள் அனைத்து பாடங்களிலும் தேர்ச்சி பெற்றனர் (தேர்ச்சி மதிப்பெண் 35). {n} மாணவர்கள் குறைந்தது ஒரு பாடத்தில் தோல்வி."),
    "e_group": ("By {col}: \"{top}\" has the best average ({a}); \"{low}\" has the lowest ({b}).",
                "{col} வாரியாக: \"{top}\" சிறந்த சராசரி ({a}); \"{low}\" குறைவான சராசரி ({b})."),
    "e_att": ("Students with higher attendance score higher marks (relationship {r}).",
              "அதிக வருகை உள்ள மாணவர்கள் அதிக மதிப்பெண் பெறுகின்றனர் (தொடர்பு {r})."),
    "e_attlow": ("{n} students have attendance below 75%.", "{n} மாணவர்களின் வருகை 75%-க்கும் குறைவு."),
    "a_weak": ("Arrange extra classes for {worst}, the weakest subject.", "பலவீனமான பாடமான {worst}-க்கு கூடுதல் வகுப்புகள் நடத்துங்கள்."),
    "a_support": ("Meet the parents of the {n} students who need support and set a revision plan for each.",
                  "உதவி தேவைப்படும் {n} மாணவர்களின் பெற்றோரைச் சந்தித்து ஒவ்வொருவருக்கும் திருப்புதல் திட்டம் அமையுங்கள்."),
    "a_att": ("Follow up on low-attendance students first; it is the cheapest way to raise marks.",
              "குறைந்த வருகை உள்ள மாணவர்களை முதலில் கவனியுங்கள்; மதிப்பெண்ணை உயர்த்த இது மலிவான வழி."),
    "a_group": ("Learn from \"{top}\" ({col}) and share its method with \"{low}\".",
                "\"{top}\" ({col}) முறையைப் பகிர்ந்து \"{low}\"-க்கு உதவுங்கள்."),
    "t_top": ("Top students", "முதன்மை மாணவர்கள்"), "t_help": ("Students who need support", "உதவி தேவைப்படும் மாணவர்கள்"),
    "t_subj": ("Subject summary", "பாட சுருக்கம்"),
    # manufacturing
    "m_rate": ("Defect rate is {r}% ({d} defects out of {o} made).", "குறைபாடு விகிதம் {r}% ({o}-இல் {d} குறைபாடுகள்)."),
    "m_worst": ("In {col}, \"{w}\" has the highest defect rate ({r}%); \"{b}\" has the lowest ({r2}%).",
                "{col} பிரிவில் \"{w}\" அதிக குறைபாடு விகிதம் ({r}%); \"{b}\" குறைவு ({r2}%)."),
    "m_out": ("In {col}, \"{top}\" makes the most ({o}); \"{low}\" makes the least ({o2}).",
              "{col} பிரிவில் \"{top}\" அதிகம் உற்பத்தி செய்கிறது ({o}); \"{low}\" குறைவு ({o2})."),
    "m_down": ("Downtime is highest in {col} \"{g}\" ({d} in total).", "{col} \"{g}\"-இல் செயலிழப்பு நேரம் அதிகம் (மொத்தம் {d})."),
    "a_defect": ("Inspect \"{w}\" ({col}) first: it makes the most faulty pieces for every unit produced.",
                 "முதலில் \"{w}\" ({col})-ஐ ஆய்வு செய்யுங்கள்: அது அதிக குறைபாடுள்ள பொருட்களை உருவாக்குகிறது."),
    "a_target": ("Set a target defect rate below 2% and check it every week.", "குறைபாடு விகிதத்தை 2%-க்கு கீழ் இலக்காக வைத்து வாரந்தோறும் சரிபாருங்கள்."),
    "a_down": ("Plan maintenance for \"{g}\" to cut downtime.", "செயலிழப்பைக் குறைக்க \"{g}\"-க்கு பராமரிப்பு திட்டமிடுங்கள்."),
    "t_group": ("{col}: output and defects", "{col}: உற்பத்தி மற்றும் குறைபாடுகள்"),
    # company
    "h_head": ("{n} people in the file. Total pay {tot}, average {avg}, middle (median) {med}.",
               "கோப்பில் {n} பேர் உள்ளனர். மொத்த ஊதியம் {tot}, சராசரி {avg}, இடைநிலை {med}."),
    "h_dept": ("In {col}, \"{top}\" has the highest average {m} ({a}); \"{low}\" has the lowest ({b}).",
               "{col} பிரிவில் \"{top}\" அதிக சராசரி {m} ({a}); \"{low}\" குறைவு ({b})."),
    "h_spread": ("{m} varies a lot inside \"{g}\" (highest {mx}, lowest {mn}). Check that pay is fair.",
                 "\"{g}\"-க்குள் {m} மிகவும் மாறுபடுகிறது (அதிகம் {mx}, குறைவு {mn}). ஊதியம் நியாயமா எனப் பாருங்கள்."),
    "h_exp": ("{m} rises with {e} (relationship {r}), so pay follows experience.",
              "{e} உயர {m} உயர்கிறது (தொடர்பு {r}); ஊதியம் அனுபவத்தைப் பின்பற்றுகிறது."),
    "h_noexp": ("{m} does not clearly follow {e} (relationship {r}). Review your pay rules.",
                "{m} என்பது {e}-ஐ தெளிவாகப் பின்பற்றவில்லை (தொடர்பு {r}). ஊதிய விதிகளை மறுபரிசீலனை செய்யுங்கள்."),
    "h_attr": ("{p}% of people have left or are leaving.", "{p}% பேர் வெளியேறியுள்ளனர் அல்லது வெளியேறுகின்றனர்."),
    "h_hours": ("In {col}, \"{g}\" works the longest hours (average {a}).", "{col} பிரிவில் \"{g}\" அதிக நேரம் வேலை செய்கிறது (சராசரி {a})."),
    "a_attr": ("Find out why people leave (pay, manager, workload) and fix the top reason first.",
               "ஆட்கள் ஏன் வெளியேறுகிறார்கள் (ஊதியம், மேலாளர், பணிச்சுமை) எனக் கண்டறிந்து முதல் காரணத்தை சரிசெய்யுங்கள்."),
    "a_pay": ("Review pay inside \"{g}\" so similar roles earn similar amounts.", "ஒத்த பணிகளுக்கு ஒத்த ஊதியம் கிடைக்க \"{g}\"-இல் ஊதியத்தைச் சரிபாருங்கள்."),
    "a_hours": ("Check workload in \"{g}\" to avoid burnout.", "அதிக சுமையைத் தவிர்க்க \"{g}\"-இல் பணிச்சுமையைச் சரிபாருங்கள்."),
    "t_dept": ("{col}: people and pay", "{col}: நபர்கள் மற்றும் ஊதியம்"),
    # healthcare
    "p_top": ("Most common {col}: \"{top}\" ({share}% of visits).", "அதிகம் காணப்படும் {col}: \"{top}\" ({share}% வருகைகள்)."),
    "p_age": ("{kids}% are children (under 13) and {old}% are 60 or older.", "{kids}% குழந்தைகள் (13-க்கு கீழ்); {old}% பேர் 60 அல்லது அதற்கு மேல்."),
    "p_rep": ("{n} patients came more than once ({p}% of patients).", "{n} நோயாளிகள் ஒன்றுக்கு மேற்பட்ட முறை வந்தனர் ({p}%)."),
    "a_rep": ("Send follow-up reminders to repeat patients; they trust you already.", "மீண்டும் வரும் நோயாளிகளுக்கு நினைவூட்டல் அனுப்புங்கள்."),
    "a_old": ("Keep time and supplies ready for senior citizens (BP and sugar checks).", "மூத்தவர்களுக்கு (BP, சர்க்கரை பரிசோதனை) நேரமும் பொருட்களும் தயாராக வைத்திருங்கள்."),
    # finance
    "f_net": ("Income {i}, expenses {e}, balance {n}.", "வருமானம் {i}, செலவு {e}, மீதம் {n}."),
    "f_loss": ("You are spending more than you earn in this file.", "இந்த கோப்பில் வருமானத்தை விட செலவு அதிகம்."),
    "f_top": ("Biggest spending group in {col}: \"{g}\" ({share}% of expenses).", "{col} பிரிவில் அதிகம் செலவாவது: \"{g}\" ({share}% செலவு)."),
    "a_cut": ("Look at \"{g}\" first when you want to cut costs.", "செலவு குறைக்க முதலில் \"{g}\"-ஐ பாருங்கள்."),
    # logistics
    "l_late": ("{p}% of deliveries were late.", "{p}% விநியோகங்கள் தாமதமாயின."),
    "l_worst": ("In {col}, \"{g}\" has the most delays ({p}% late).", "{col} பிரிவில் \"{g}\" அதிக தாமதம் ({p}%)."),
    "a_late": ("Fix \"{g}\" ({col}) first: it causes the most late deliveries.", "முதலில் \"{g}\" ({col})-ஐ சரிசெய்யுங்கள்: அது அதிக தாமதத்தை உண்டாக்குகிறது."),
}


def T(key, lang, **kw):
    en, ta = TX[key]
    return (ta if lang == "ta" else en).format(**kw)


def Hd(key, lang):
    return H[key][1 if lang == "ta" else 0]


# ----------------------------------------------------------------- helpers
def detect(df):
    keys = [_key(c) for c in df.columns]
    scores = {ind: sum(any(w in k for w in ws) for k in keys) for ind, ws in WORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


def _find(df, kinds, words, want=("number",), exclude=()):
    for c in df.columns:
        k = _key(c)
        if kinds[c] in want and any(w in k for w in words) and not any(w in k for w in exclude):
            return c
    return None


def _groups(df, kinds, words, limit=2, skip=()):
    named = [c for c in df.columns if kinds[c] in ("category",) and c not in skip
             and any(w in _key(c) for w in words) and 2 <= df[c].nunique() <= 30]
    if named:
        return named[:limit]
    other = [c for c in df.columns if kinds[c] == "category" and c not in skip and 2 <= df[c].nunique() <= 12]
    return other[:1]


def _name_col(df, kinds):
    for c in df.columns:
        if "name" in _key(c) and kinds[c] in ("id", "text", "category"):
            return c
    for c in df.columns:
        if kinds[c] in ("text", "id") and "roll" not in _key(c) and df[c].dtype == object:
            return c
    return None


def _rows(df_rows):
    return [[(fmt(x) if isinstance(x, (int, float, np.floating, np.integer)) and not isinstance(x, bool) else str(x))
             for x in r] for r in df_rows]


# ----------------------------------------------------------------- education
def _education(df, kinds, lang):
    F, A, TB = [], [], []
    nums = [c for c in df.columns if kinds[c] == "number"]
    att = [c for c in nums if any(w in _key(c) for w in ("attend", "present"))]
    bad = ("age", "rank", "total", "percent", "average", "avg", "roll", "year", "sem", "cgpa", "gpa", "fee")
    subj = []
    for c in nums:
        if c in att or any(w in _key(c) for w in bad):
            continue
        v = df[c].dropna()
        if len(v) and v.between(0, 100).mean() >= 0.95 and v.nunique() > 5:
            subj.append(c)
    if not subj:
        return F, A, TB
    stats = []
    for c in subj:
        v = df[c].dropna()
        stats.append((c, float(v.mean()), float((v >= 35).mean() * 100), float(v.max()), float(v.min())))
    stats.sort(key=lambda x: -x[1])
    if len(stats) >= 2:
        best, worst = stats[0], stats[-1]
        F.append(("info", T("e_subject", lang, best=best[0], a=fmt(best[1]), worst=worst[0], b=fmt(worst[1]), p=fmt(worst[2]))))
        A.append(T("a_weak", lang, worst=worst[0]))
    TB.append({"title": T("t_subj", lang),
               "cols": [Hd("subject", lang), Hd("avg", lang), Hd("pass", lang), Hd("high", lang), Hd("low", lang)],
               "rows": _rows([[s[0], round(s[1], 1), round(s[2]), s[3], s[4]] for s in stats])})
    marks = df[subj]
    avg = marks.mean(axis=1)
    failed = (marks < 35).sum(axis=1)
    n = len(df)
    nfail = int((failed > 0).sum())
    F.append(("good" if nfail / max(n, 1) < 0.1 else "warn",
              T("e_pass", lang, p=round((n - nfail) / max(n, 1) * 100), n=nfail)))
    name = _name_col(df, kinds)
    label = df[name].astype(str) if name else pd.Series([f"#{i + 1}" for i in range(n)], index=df.index)
    top = avg.sort_values(ascending=False).head(5)
    TB.append({"title": T("t_top", lang), "cols": [Hd("name", lang), Hd("avg", lang)],
               "rows": _rows([[label[i], round(avg[i], 1)] for i in top.index])})
    need = df.index[(failed > 0) | (avg < 40)]
    if len(need):
        order = sorted(need, key=lambda i: (-failed[i], avg[i]))[:8]
        TB.append({"title": T("t_help", lang), "cols": [Hd("name", lang), Hd("avg", lang), Hd("failed", lang)],
                   "rows": _rows([[label[i], round(avg[i], 1), int(failed[i])] for i in order])})
        A.append(T("a_support", lang, n=len(need)))
    for g in _groups(df, kinds, ("class", "section", "dept", "department", "batch", "group", "course", "gender"), 2):
        ga = avg.groupby(df[g]).mean().dropna().sort_values(ascending=False)
        if len(ga) >= 2:
            F.append(("info", T("e_group", lang, col=g, top=str(ga.index[0]), a=fmt(ga.iloc[0]), low=str(ga.index[-1]), b=fmt(ga.iloc[-1]))))
            if "gender" not in _key(g):
                A.append(T("a_group", lang, top=str(ga.index[0]), col=g, low=str(ga.index[-1])))
    if att:
        a = df[att[0]]
        r = a.corr(avg)
        if pd.notna(r) and r >= 0.3:
            F.append(("info", T("e_att", lang, r=round(float(r), 2))))
            A.append(T("a_att", lang))
        low = int((a < 75).sum())
        if low:
            F.append(("warn", T("e_attlow", lang, n=low)))
    return F, A, TB


# ----------------------------------------------------------------- manufacturing
def _manufacturing(df, kinds, lang):
    F, A, TB = [], [], []
    out = _find(df, kinds, ("produced", "production", "output", "units", "quantity", "qty"), exclude=("defect", "reject", "scrap"))
    dfc = _find(df, kinds, ("defect", "reject", "scrap", "rework", "fail"))
    dn = _find(df, kinds, ("downtime", "idle", "breakdown", "stoppage"))
    if not out and not dfc and not dn:
        return F, A, TB
    if out and dfc and df[out].sum() > 0:
        rate = df[dfc].sum() / df[out].sum() * 100
        F.append(("warn" if rate > 3 else "good", T("m_rate", lang, r=round(float(rate), 2), d=fmt(df[dfc].sum()), o=fmt(df[out].sum()))))
        A.append(T("a_target", lang))
    skip = [c for c in (out, dfc, dn) if c]
    for g in _groups(df, kinds, ("machine", "line", "shift", "plant", "operator", "product", "batch", "unit", "supervisor"), 2, skip):
        agg = {}
        if out:
            agg["o"] = df.groupby(g)[out].sum()
        if dfc:
            agg["d"] = df.groupby(g)[dfc].sum()
        if dn:
            agg["w"] = df.groupby(g)[dn].sum()
        t = pd.DataFrame(agg).dropna(how="all")
        if len(t) < 2:
            continue
        if out and dfc:
            t["r"] = t["d"] / t["o"].replace(0, np.nan) * 100
            r = t["r"].dropna().sort_values(ascending=False)
            if len(r) >= 2:
                F.append(("warn", T("m_worst", lang, col=g, w=str(r.index[0]), r=round(float(r.iloc[0]), 2),
                                    b=str(r.index[-1]), r2=round(float(r.iloc[-1]), 2))))
                A.append(T("a_defect", lang, w=str(r.index[0]), col=g))
        if out:
            o = t["o"].sort_values(ascending=False)
            F.append(("info", T("m_out", lang, col=g, top=str(o.index[0]), o=fmt(o.iloc[0]), low=str(o.index[-1]), o2=fmt(o.iloc[-1]))))
        if dn:
            w = t["w"].sort_values(ascending=False)
            if w.iloc[0] > 0:
                F.append(("warn", T("m_down", lang, col=g, g=str(w.index[0]), d=fmt(w.iloc[0]))))
                A.append(T("a_down", lang, g=str(w.index[0])))
        cols = [g] + ([Hd("output", lang)] if out else []) + ([Hd("defects", lang), Hd("rate", lang)] if dfc else []) + ([Hd("down", lang)] if dn else [])
        rows = []
        for idx, rw in t.iterrows():
            line = [str(idx)]
            if out:
                line.append(rw["o"])
            if dfc:
                line += [rw["d"], round(float(rw["r"]), 2) if "r" in t and pd.notna(rw.get("r")) else ""]
            if dn:
                line.append(rw["w"])
            rows.append(line)
        TB.append({"title": T("t_group", lang, col=g), "cols": cols, "rows": _rows(rows)})
    return F, A, TB


# ----------------------------------------------------------------- company / staff
def _company(df, kinds, lang):
    F, A, TB = [], [], []
    sal = _find(df, kinds, ("salary", "ctc", "pay", "wage"))
    hrs = _find(df, kinds, ("hours", "hrs"))
    exp = _find(df, kinds, ("experience", "exp", "tenure", "years"))
    n = len(df)
    if sal:
        v = df[sal].dropna()
        F.append(("info", T("h_head", lang, n=f"{n:,}", tot=fmt(v.sum()), avg=fmt(v.mean()), med=fmt(v.median()))))
    for g in _groups(df, kinds, ("department", "dept", "team", "designation", "role", "location", "branch", "project"), 2, [c for c in (sal, hrs, exp) if c]):
        if sal:
            gs = df.groupby(g)[sal].agg(["count", "mean", "max", "min"]).dropna()
            if len(gs) >= 2:
                s = gs.sort_values("mean", ascending=False)
                F.append(("info", T("h_dept", lang, col=g, m=sal, top=str(s.index[0]), a=fmt(s["mean"].iloc[0]), low=str(s.index[-1]), b=fmt(s["mean"].iloc[-1]))))
                wide = gs[(gs["count"] >= 3) & (gs["min"] > 0) & (gs["max"] / gs["min"] >= 3)]
                if len(wide):
                    gname = str(wide.index[0])
                    F.append(("warn", T("h_spread", lang, m=sal, g=gname, mx=fmt(wide["max"].iloc[0]), mn=fmt(wide["min"].iloc[0]))))
                    A.append(T("a_pay", lang, g=gname))
                TB.append({"title": T("t_dept", lang, col=g), "cols": [g, Hd("people", lang), Hd("pay", lang)],
                           "rows": _rows([[str(i), int(r["count"]), round(float(r["mean"]))] for i, r in s.iterrows()])})
        if hrs:
            hs = df.groupby(g)[hrs].mean().dropna().sort_values(ascending=False)
            if len(hs) >= 2 and hs.iloc[0] > hs.mean() * 1.15:
                F.append(("warn", T("h_hours", lang, col=g, g=str(hs.index[0]), a=fmt(hs.iloc[0]))))
                A.append(T("a_hours", lang, g=str(hs.index[0])))
    if sal and exp:
        r = df[sal].corr(df[exp])
        if pd.notna(r):
            if r >= 0.5:
                F.append(("good", T("h_exp", lang, m=sal, e=exp, r=round(float(r), 2))))
            elif abs(r) < 0.2:
                F.append(("warn", T("h_noexp", lang, m=sal, e=exp, r=round(float(r), 2))))
    for c in df.columns:
        if kinds[c] == "category" and any(w in _key(c) for w in ("attrition", "resign", "exit", "left", "status")):
            vals = df[c].astype(str).str.strip().str.lower()
            rate = vals.isin({"yes", "y", "1", "true", "left", "resigned", "exited", "inactive", "terminated"}).mean() * 100
            if rate > 0:
                F.append(("warn" if rate >= 10 else "info", T("h_attr", lang, p=round(float(rate), 1))))
                A.append(T("a_attr", lang))
                break
    return F, A, TB


# ----------------------------------------------------------------- clinic
def _healthcare(df, kinds, lang):
    F, A = [], []
    for c in df.columns:
        if kinds[c] == "category" and any(w in _key(c) for w in ("diagnosis", "disease", "treatment", "complaint", "symptom")):
            vc = df[c].value_counts()
            F.append(("info", T("p_top", lang, col=c, top=str(vc.index[0]), share=round(float(vc.iloc[0]) / len(df) * 100))))
            break
    age = _find(df, kinds, ("age",), exclude=("page", "usage", "image"))
    if age:
        v = df[age].dropna()
        if len(v):
            kids, old = round(float((v < 13).mean() * 100)), round(float((v >= 60).mean() * 100))
            F.append(("info", T("p_age", lang, kids=kids, old=old)))
            if old >= 25:
                A.append(T("a_old", lang))
    pid = next((c for c in df.columns if "patient" in _key(c) and kinds[c] in ("id", "text", "category", "number")
                and df[c].nunique() < len(df)), None)
    if pid:
        vc = df[pid].value_counts()
        rep = int((vc > 1).sum())
        if rep:
            F.append(("info", T("p_rep", lang, n=rep, p=round(rep / len(vc) * 100))))
            A.append(T("a_rep", lang))
    return F, A, []


# ----------------------------------------------------------------- accounts
def _finance(df, kinds, lang):
    F, A = [], []
    inc = _find(df, kinds, ("income", "credit", "receipt", "revenue"))
    exp = _find(df, kinds, ("expense", "debit", "spend", "payment"))
    i = e = None
    if inc and exp and inc != exp:
        i, e = float(df[inc].sum()), float(df[exp].sum())
    else:
        amt = _find(df, kinds, ("amount", "value"))
        typ = next((c for c in df.columns if kinds[c] == "category" and any(w in _key(c) for w in ("type", "dr", "cr", "kind"))), None)
        if amt and typ:
            tv = df[typ].astype(str).str.lower()
            i = float(df.loc[tv.str.contains("income|credit|receipt|cr", regex=True), amt].sum())
            e = float(df.loc[tv.str.contains("expense|debit|payment|dr", regex=True), amt].sum())
    if i is None:
        return F, A, []
    F.append(("good" if i >= e else "warn", T("f_net", lang, i=fmt(i), e=fmt(e), n=fmt(i - e))))
    if e > i:
        F.append(("warn", T("f_loss", lang)))
    for g in _groups(df, kinds, ("category", "head", "type", "account", "payee", "mode"), 1):
        col = exp or _find(df, kinds, ("amount", "value"))
        if col:
            gs = df.groupby(g)[col].sum().sort_values(ascending=False)
            if len(gs) >= 2 and gs.sum() > 0:
                F.append(("info", T("f_top", lang, col=g, g=str(gs.index[0]), share=round(float(gs.iloc[0] / gs.sum() * 100)))))
                A.append(T("a_cut", lang, g=str(gs.index[0])))
    return F, A, []


# ----------------------------------------------------------------- delivery
def _logistics(df, kinds, lang):
    F, A, TB = [], [], []
    late = None
    dl = _find(df, kinds, ("delay", "late"))
    if dl:
        late = df[dl] > 0
    else:
        for c in df.columns:
            if kinds[c] == "category" and any(w in _key(c) for w in ("status", "ontime", "delivery")):
                late = df[c].astype(str).str.lower().str.contains("late|delay")
                break
    if late is None or late.sum() == 0:
        return F, A, TB
    F.append(("warn" if late.mean() > 0.1 else "good", T("l_late", lang, p=round(float(late.mean() * 100), 1))))
    for g in _groups(df, kinds, ("route", "vehicle", "driver", "area", "city", "zone", "carrier"), 1):
        gp = late.groupby(df[g]).mean().sort_values(ascending=False) * 100
        if len(gp) >= 2 and gp.iloc[0] > 0:
            F.append(("warn", T("l_worst", lang, col=g, g=str(gp.index[0]), p=round(float(gp.iloc[0]), 1))))
            A.append(T("a_late", lang, g=str(gp.index[0]), col=g))
    return F, A, TB


RUN = {"education": _education, "manufacturing": _manufacturing, "company": _company,
       "healthcare": _healthcare, "finance": _finance, "logistics": _logistics}


def analyse_industry(df, kinds, lang="en"):
    kind = detect(df)
    if not kind:
        return None
    try:
        res = RUN[kind](df, kinds, lang)
        F, A = res[0], res[1]
        TB = res[2] if len(res) > 2 else []
    except Exception:          # never break the report because of an industry rule
        return None
    if not F and not TB:
        return None
    label = LABEL[kind][1 if lang == "ta" else 0]
    return {"kind": kind, "label": label, "intro": T("label", lang, x=label),
            "findings": [{"tone": a, "text": b} for a, b in F], "actions": A, "tables": TB}


# =================================================================== more data types
WORDS.update({
    "sales": ("sales", "profit", "revenue", "product", "price", "units", "margin", "discount", "sold", "item"),
    "customers": ("customer", "age", "preference", "feedback", "rating", "satisfaction", "loyalty", "gender", "purchase", "review"),
    "ecommerce": ("order", "return", "refund", "cart", "shipping", "coupon", "cancel", "sku", "delivered"),
    "marketing": ("campaign", "impression", "click", "conversion", "ctr", "cpc", "lead", "channel", "adspend", "signup"),
    "social": ("like", "comment", "share", "view", "follower", "post", "reach", "engagement", "hashtag", "reel"),
    "website": ("visitor", "session", "pageview", "bounce", "traffic", "page", "source", "device", "click", "duration"),
    "agriculture": ("crop", "soil", "rainfall", "yield", "irrigation", "fertilizer", "pest", "harvest", "humidity", "moisture", "acre", "farm"),
})
WORDS["logistics"] = WORDS["logistics"] + ("fuel", "traffic", "travel", "speed", "mileage", "km", "duration")
WORDS["healthcare"] = WORDS["healthcare"] + ("outcome", "recovery", "symptom", "hospital")
LABEL.update({
    "sales": ("Sales data", "விற்பனை தரவு"), "customers": ("Customer data", "வாடிக்கையாளர் தரவு"),
    "ecommerce": ("E-commerce data", "இ-காமர்ஸ் தரவு"), "marketing": ("Marketing data", "சந்தைப்படுத்தல் தரவு"),
    "social": ("Social media data", "சமூக ஊடக தரவு"), "website": ("Website data", "இணையதள தரவு"),
    "agriculture": ("Agriculture data", "விவசாய தரவு"),
})
H.update({"product": ("Product", "பொருள்"), "profit": ("Profit", "லாபம்"), "perunit": ("Profit per unit", "ஒரு யூனிட் லாபம்"),
          "returns": ("Returns %", "திரும்பல் %"), "cpc": ("Cost per result", "ஒரு பலனுக்கான செலவு"),
          "eng": ("Avg engagement", "சராசரி ஈடுபாடு"), "bounce": ("Bounce %", "வெளியேறல் %"),
          "visits": ("Visits", "வருகைகள்"), "yield": ("Average yield", "சராசரி விளைச்சல்"), "time": ("Avg time", "சராசரி நேரம்"),
          "fuel": ("Fuel per distance", "தூரத்துக்கான எரிபொருள்"), "success": ("Success %", "வெற்றி %")})
TX.update({
    # sales
    "s_top": ("Highest {m}: \"{a}\". Highest profit: \"{b}\".", "அதிக {m}: \"{a}\". அதிக லாபம்: \"{b}\"."),
    "s_period": ("{p} has the highest profit ({v}); {q} has the lowest ({w}).", "{p} மாதத்தில் லாபம் அதிகம் ({v}); {q} மாதத்தில் குறைவு ({w})."),
    "s_unit": ("Profit per unit sold: \"{a}\" earns {x}; \"{b}\" earns {y}.", "ஒரு யூனிட்டுக்கு லாபம்: \"{a}\" {x}; \"{b}\" {y}."),
    "s_margin": ("Profit is {r}% of revenue overall.", "மொத்த வருவாயில் லாபம் {r}%."),
    "a_stock": ("Stock more of \"{b}\": it earns the most profit.", "\"{b}\"-ஐ அதிகம் வாங்கி வையுங்கள்: அது அதிக லாபம் தருகிறது."),
    "a_check": ("\"{a}\" sells the most but \"{b}\" earns more profit. Check the price and cost of \"{a}\".",
                "\"{a}\" அதிகம் விற்கிறது ஆனால் \"{b}\" அதிக லாபம் தருகிறது. \"{a}\" விலை மற்றும் செலவைச் சரிபாருங்கள்."),
    "t_prod": ("{col}: sales and profit", "{col}: விற்பனை மற்றும் லாபம்"),
    # customers
    "c_age": ("Most customers are aged {g} ({p}%).", "பெரும்பாலான வாடிக்கையாளர்கள் {g} வயதினர் ({p}%)."),
    "c_pref": ("Most popular {col}: \"{top}\" ({p}% of customers).", "அதிகம் விரும்பப்படும் {col}: \"{top}\" ({p}% வாடிக்கையாளர்கள்)."),
    "c_rate": ("Average {col} is {a}. {p}% of customers gave a low score.", "சராசரி {col} {a}. {p}% வாடிக்கையாளர்கள் குறைந்த மதிப்பெண் அளித்தனர்."),
    "c_low": ("In {col}, \"{g}\" is least satisfied (average {a}).", "{col} பிரிவில் \"{g}\" குறைவாக திருப்தியடைந்துள்ளனர் (சராசரி {a})."),
    "a_age": ("Aim your offers and messages at the {g} age group first.", "உங்கள் சலுகைகளையும் செய்திகளையும் முதலில் {g} வயதினருக்கு அனுப்புங்கள்."),
    "a_unhappy": ("Call a few unhappy customers in \"{g}\" and ask what went wrong.", "\"{g}\" பிரிவில் அதிருப்தியான சில வாடிக்கையாளர்களை அழைத்து என்ன தவறு என்று கேளுங்கள்."),
    # ecommerce
    "ec_ret": ("{p}% of orders were returned or refunded.", "{p}% ஆர்டர்கள் திரும்பப்பெறப்பட்டன அல்லது பணம் திருப்பப்பட்டன."),
    "ec_worst": ("In {col}, \"{g}\" has the most returns ({p}%).", "{col} பிரிவில் \"{g}\" அதிக திரும்பல் ({p}%)."),
    "ec_cancel": ("{p}% of orders were cancelled.", "{p}% ஆர்டர்கள் ரத்து செய்யப்பட்டன."),
    "a_ret": ("Check quality, size or description of \"{g}\" ({col}); it is returned the most.", "\"{g}\" ({col}) அதிகம் திரும்புகிறது; தரம், அளவு அல்லது விளக்கத்தைச் சரிபாருங்கள்."),
    # marketing
    "mk_ctr": ("Click rate is {r}% ({c} clicks from {i} views).", "கிளிக் விகிதம் {r}% ({i} பார்வைகளில் {c} கிளிக்குகள்)."),
    "mk_conv": ("{r}% of clicks turned into results ({n} in total).", "{r}% கிளிக்குகள் பலனாக மாறின (மொத்தம் {n})."),
    "mk_cost": ("Each result costs about {c}.", "ஒரு பலனுக்கு சுமார் {c} செலவாகிறது."),
    "mk_best": ("In {col}, \"{b}\" gives the cheapest results ({x}); \"{w}\" the most expensive ({y}).", "{col} பிரிவில் \"{b}\" மலிவான பலன் ({x}); \"{w}\" விலை உயர்ந்தது ({y})."),
    "a_budget": ("Move some budget from \"{w}\" to \"{b}\" ({col}).", "\"{w}\"-இலிருந்து சிறிது பட்ஜெட்டை \"{b}\"-க்கு ({col}) மாற்றுங்கள்."),
    # social
    "so_rate": ("Average engagement is {r}% of views.", "சராசரி ஈடுபாடு பார்வைகளில் {r}%."),
    "so_best": ("In {col}, \"{g}\" gets the most engagement (average {a}); \"{l}\" gets the least ({b}).", "{col} பிரிவில் \"{g}\" அதிக ஈடுபாடு (சராசரி {a}); \"{l}\" குறைவு ({b})."),
    "so_day": ("Posts made on {day} get the most engagement.", "{day} அன்று இடும் பதிவுகளுக்கு அதிக ஈடுபாடு கிடைக்கிறது."),
    "so_top": ("Top post: \"{n}\" with {e} engagement.", "சிறந்த பதிவு: \"{n}\" ({e} ஈடுபாடு)."),
    "a_content": ("Post more \"{g}\" content ({col}); people respond to it most.", "\"{g}\" ({col}) உள்ளடக்கத்தை அதிகம் பதியுங்கள்; மக்கள் அதற்கு அதிகம் பதிலளிக்கிறார்கள்."),
    "a_postday": ("Schedule your best posts on {day}.", "உங்கள் சிறந்த பதிவுகளை {day} அன்று திட்டமிடுங்கள்."),
    # website
    "wb_vis": ("Total {col}: {n}.", "மொத்த {col}: {n}."),
    "wb_bounce": ("Average bounce rate is {r}%. {note}", "சராசரி வெளியேறல் விகிதம் {r}%. {note}"),
    "wb_hi": ("That is high: many visitors leave without looking around.", "இது அதிகம்: பலர் எதையும் பார்க்காமல் வெளியேறுகின்றனர்."),
    "wb_ok": ("That is healthy.", "இது ஆரோக்கியமான நிலை."),
    "wb_top": ("In {col}, \"{g}\" brings the most visits ({p}%).", "{col} பிரிவில் \"{g}\" அதிக வருகைகளைத் தருகிறது ({p}%)."),
    "wb_worst": ("In {col}, \"{g}\" has the highest bounce rate ({r}%).", "{col} பிரிவில் \"{g}\" அதிக வெளியேறல் விகிதம் ({r}%)."),
    "a_bounce": ("Improve \"{g}\" ({col}): make the page faster and the next step clearer.", "\"{g}\" ({col})-ஐ மேம்படுத்துங்கள்: பக்கத்தை வேகமாக்கி அடுத்த படியைத் தெளிவாக்குங்கள்."),
    "a_source": ("Put more effort into \"{g}\" ({col}); it already brings the most visitors.", "\"{g}\" ({col})-இல் அதிக முயற்சி செலுத்துங்கள்; அது ஏற்கனவே அதிக வருகையாளர்களைத் தருகிறது."),
    # agriculture
    "ag_crop": ("In {col}, \"{b}\" gives the best {y} ({x}); \"{w}\" gives the lowest ({z}).", "{col} பிரிவில் \"{b}\" சிறந்த {y} ({x}); \"{w}\" குறைவு ({z})."),
    "ag_corr": ("{y} rises with {x} (relationship {r}).", "{x} உயர {y} உயர்கிறது (தொடர்பு {r})."),
    "ag_corr_neg": ("{y} falls when {x} goes up (relationship {r}).", "{x} உயரும்போது {y} குறைகிறது (தொடர்பு {r})."),
    "ag_irrig": ("{y} is {p}% lower when {x} is in its lowest third. Water or feed before it gets that low.", "{x} மிகக் குறைவாக இருக்கும்போது {y} {p}% குறைவு. அந்த நிலைக்கு முன்பே நீர் அல்லது உரம் கொடுங்கள்."),
    "ag_pest": ("Most common {col}: \"{g}\" ({p}% of records).", "அதிகம் காணப்படும் {col}: \"{g}\" ({p}% பதிவுகள்)."),
    "a_pest": ("Plan control for \"{g}\" before the next season.", "அடுத்த பருவத்துக்கு முன் \"{g}\"-க்கான கட்டுப்பாட்டைத் திட்டமிடுங்கள்."),
    "a_cropbest": ("Grow more of \"{b}\" where conditions are similar.", "ஒத்த சூழலில் \"{b}\"-ஐ அதிகம் பயிரிடுங்கள்."),
    # healthcare outcome / transport
    "p_eff": ("Best results for {col}: \"{b}\" ({x}% success); lowest: \"{w}\" ({y}%).", "{col}-இல் சிறந்த பலன்: \"{b}\" ({x}% வெற்றி); குறைவு: \"{w}\" ({y}%)."),
    "tr_time": ("On {col}, \"{b}\" is the fastest (average {x}); \"{w}\" is the slowest ({y}).", "{col} பிரிவில் \"{b}\" வேகமானது (சராசரி {x}); \"{w}\" மெதுவானது ({y})."),
    "tr_fuel": ("On {col}, \"{b}\" uses the least fuel for the distance; \"{w}\" uses the most.", "{col} பிரிவில் \"{b}\" தூரத்துக்கு குறைந்த எரிபொருள்; \"{w}\" அதிகம்."),
    "a_route": ("Prefer \"{b}\" ({col}) when you can; it saves time.", "முடிந்தவரை \"{b}\" ({col})-ஐப் பயன்படுத்துங்கள்; நேரம் மிச்சமாகும்."),
})


def _truthy(series):
    v = series.astype(str).str.strip().str.lower()
    return v.isin({"yes", "y", "1", "true", "returned", "refunded", "return", "refund", "cancelled", "canceled"}) | v.str.contains("return|refund")


def _best_worst(ser):
    ser = ser.dropna().sort_values(ascending=False)
    return (ser.index[0], float(ser.iloc[0]), ser.index[-1], float(ser.iloc[-1])) if len(ser) >= 2 else None


def _sales(df, kinds, lang):
    F, A, TB = [], [], []
    from datareport import _period_keys
    profit = _find(df, kinds, ("profit", "margin", "gain"))
    sales = _find(df, kinds, ("sales", "revenue", "amount", "units", "sold", "qty", "quantity", "turnover"), exclude=("profit",))
    revenue = _find(df, kinds, ("revenue", "turnover", "amount"), exclude=("profit",))
    units = _find(df, kinds, ("units", "sold", "qty", "quantity", "sales"), exclude=("profit", "revenue", "amount"))
    if not sales and not profit:
        return F, A, TB
    gcols = _groups(df, kinds, ("product", "item", "category", "brand", "branch", "store", "region"), 1,
                    [c for c in (sales, profit) if c])
    if gcols:
        g = gcols[0]
        agg = {}
        if sales:
            agg["s"] = df.groupby(g)[sales].sum()
        if profit:
            agg["p"] = df.groupby(g)[profit].sum()
        tb = pd.DataFrame(agg)
        a = _best_worst(tb["s"]) if sales else None
        b = _best_worst(tb["p"]) if profit else None
        if a and b:
            F.append(("info", T("s_top", lang, m=sales, a=str(a[0]), b=str(b[0]))))
            if str(a[0]) != str(b[0]):
                A.append(T("a_check", lang, a=str(a[0]), b=str(b[0])))
            A.append(T("a_stock", lang, b=str(b[0])))
        elif b:
            A.append(T("a_stock", lang, b=str(b[0])))
        if profit and units:
            pu = (tb["p"] / df.groupby(g)[units].sum().replace(0, np.nan)).dropna()
            r = _best_worst(pu)
            if r:
                F.append(("info", T("s_unit", lang, a=str(r[0]), x=fmt(r[1]), b=str(r[2]), y=fmt(r[3]))))
        cols = [g] + ([sales] if sales else []) + ([Hd("profit", lang)] if profit else [])
        TB.append({"title": T("t_prod", lang, col=g), "cols": cols,
                   "rows": _rows([[str(i)] + ([r_["s"]] if sales else []) + ([r_["p"]] if profit else []) for i, r_ in tb.sort_values("p" if profit else "s", ascending=False).iterrows()])})
    if profit and revenue and df[revenue].sum() > 0 and revenue != profit:
        F.append(("info", T("s_margin", lang, r=round(float(df[profit].sum() / df[revenue].sum() * 100), 1))))
    pk = _period_keys(df, kinds)
    if profit and pk is not None:
        keys, label = pk
        pp = df.groupby(keys)[profit].sum().dropna().sort_index()
        if len(pp) >= 2:
            F.append(("info", T("s_period", lang, p=label(pp.idxmax()), v=fmt(pp.max()), q=label(pp.idxmin()), w=fmt(pp.min()))))
    return F, A, TB


def _customers(df, kinds, lang):
    F, A = [], []
    age = _find(df, kinds, ("age",), exclude=("page", "usage", "image", "stage"))
    if age:
        v = df[age].dropna()
        v = v[(v > 0) & (v < 110)]
        if len(v) >= 5:
            bins = pd.cut(v, [0, 17, 25, 40, 60, 120], labels=["under 18", "18-25", "26-40", "41-60", "over 60"])
            vc = bins.value_counts(normalize=True)
            F.append(("info", T("c_age", lang, g=str(vc.index[0]), p=round(float(vc.iloc[0] * 100)))))
            A.append(T("a_age", lang, g=str(vc.index[0])))
    for c in df.columns:
        if kinds[c] == "category" and any(w in _key(c) for w in ("preference", "favourite", "favorite", "interest", "channel", "liked", "category", "product")):
            vc = df[c].value_counts(normalize=True)
            F.append(("info", T("c_pref", lang, col=c, top=str(vc.index[0]), p=round(float(vc.iloc[0] * 100)))))
            break
    rate = _find(df, kinds, ("rating", "satisfaction", "score", "feedback", "review"))
    if rate:
        v = df[rate].dropna()
        mx = v.max()
        low = (v <= (2 if mx <= 5 else 4)).mean() * 100
        F.append(("warn" if low >= 20 else "info", T("c_rate", lang, col=rate, a=fmt(v.mean()), p=round(float(low)))))
        for g in _groups(df, kinds, ("city", "area", "gender", "segment", "product", "channel", "store"), 1, [rate]):
            m = df.groupby(g)[rate].mean().dropna().sort_values()
            if len(m) >= 2:
                F.append(("warn", T("c_low", lang, col=g, g=str(m.index[0]), a=fmt(m.iloc[0]))))
                A.append(T("a_unhappy", lang, g=str(m.index[0])))
    return F, A, []


def _ecommerce(df, kinds, lang):
    F, A = [], []
    ret = next((c for c in df.columns if any(w in _key(c) for w in ("return", "refund")) and kinds[c] in ("category", "number")), None)
    stat = next((c for c in df.columns if kinds[c] == "category" and any(w in _key(c) for w in ("status", "state"))), None)
    if ret:
        mask = (df[ret] > 0) if kinds[ret] == "number" else _truthy(df[ret])
        if mask.sum():
            F.append(("warn" if mask.mean() > 0.1 else "info", T("ec_ret", lang, p=round(float(mask.mean() * 100), 1))))
            for g in _groups(df, kinds, ("product", "category", "brand", "sku", "item"), 1, [ret]):
                gp = mask.groupby(df[g]).mean().sort_values(ascending=False) * 100
                if len(gp) >= 2 and gp.iloc[0] > 0:
                    F.append(("warn", T("ec_worst", lang, col=g, g=str(gp.index[0]), p=round(float(gp.iloc[0]), 1))))
                    A.append(T("a_ret", lang, g=str(gp.index[0]), col=g))
    if stat:
        can = df[stat].astype(str).str.lower().str.contains("cancel")
        if can.sum():
            F.append(("warn" if can.mean() > 0.1 else "info", T("ec_cancel", lang, p=round(float(can.mean() * 100), 1))))
    return F, A, []


def _marketing(df, kinds, lang):
    F, A, TB = [], [], []
    imp = _find(df, kinds, ("impression", "views", "reach"))
    clk = _find(df, kinds, ("click",))
    conv = _find(df, kinds, ("conversion", "lead", "signup", "result", "purchase", "orders"))
    spend = _find(df, kinds, ("spend", "cost", "budget"), exclude=("per",))
    if imp and clk and df[imp].sum() > 0:
        F.append(("info", T("mk_ctr", lang, r=round(float(df[clk].sum() / df[imp].sum() * 100), 2), c=fmt(df[clk].sum()), i=fmt(df[imp].sum()))))
    if clk and conv and df[clk].sum() > 0:
        F.append(("info", T("mk_conv", lang, r=round(float(df[conv].sum() / df[clk].sum() * 100), 2), n=fmt(df[conv].sum()))))
    if spend and conv and df[conv].sum() > 0:
        F.append(("info", T("mk_cost", lang, c=fmt(df[spend].sum() / df[conv].sum()))))
        for g in _groups(df, kinds, ("campaign", "channel", "platform", "source", "ad"), 1, [c for c in (imp, clk, conv, spend) if c]):
            ag = df.groupby(g)[[spend, conv]].sum()
            cpc = (ag[spend] / ag[conv].replace(0, np.nan)).dropna().sort_values()
            if len(cpc) >= 2:
                F.append(("info", T("mk_best", lang, col=g, b=str(cpc.index[0]), x=fmt(cpc.iloc[0]), w=str(cpc.index[-1]), y=fmt(cpc.iloc[-1]))))
                A.append(T("a_budget", lang, w=str(cpc.index[-1]), b=str(cpc.index[0]), col=g))
                TB.append({"title": g, "cols": [g, spend, conv, Hd("cpc", lang)],
                           "rows": _rows([[str(i), ag.loc[i, spend], ag.loc[i, conv], round(float(v), 2)] for i, v in cpc.items()])})
    return F, A, TB


def _social(df, kinds, lang):
    F, A = [], []
    lk = _find(df, kinds, ("like",)); cm = _find(df, kinds, ("comment",)); sh = _find(df, kinds, ("share",))
    vw = _find(df, kinds, ("view", "reach", "impression"))
    parts = [c for c in (lk, cm, sh) if c]
    if not parts:
        return F, A, []
    eng = df[parts].fillna(0).sum(axis=1)
    if vw and df[vw].sum() > 0:
        F.append(("info", T("so_rate", lang, r=round(float(eng.sum() / df[vw].sum() * 100), 2))))
    for g in _groups(df, kinds, ("platform", "type", "content", "category", "format", "topic", "post"), 2, parts + ([vw] if vw else [])):
        m = eng.groupby(df[g]).mean().dropna().sort_values(ascending=False)
        if len(m) >= 2:
            F.append(("info", T("so_best", lang, col=g, g=str(m.index[0]), a=fmt(m.iloc[0]), l=str(m.index[-1]), b=fmt(m.iloc[-1]))))
            A.append(T("a_content", lang, g=str(m.index[0]), col=g))
    dc = next((c for c in df.columns if kinds[c] == "date"), None)
    if dc and (df[dc].max() - df[dc].min()).days >= 14:
        wd = eng.groupby(df[dc].dt.dayofweek).mean()
        if len(wd) > 1:
            day = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][int(wd.idxmax())]
            if lang == "ta":
                try:
                    from translate import DAYS_TA
                    day = DAYS_TA.get(day, day)
                except Exception:
                    pass
            F.append(("info", T("so_day", lang, day=day)))
            A.append(T("a_postday", lang, day=day))
    nm = _name_col(df, kinds)
    if nm:
        i = eng.idxmax()
        F.append(("info", T("so_top", lang, n=str(df.loc[i, nm])[:50], e=fmt(eng.loc[i]))))
    return F, A, []


def _website(df, kinds, lang):
    F, A = [], []
    vis = _find(df, kinds, ("visitor", "session", "pageview", "users", "visits", "traffic", "views"))
    bnc = _find(df, kinds, ("bounce",))
    if vis:
        F.append(("info", T("wb_vis", lang, col=vis, n=fmt(df[vis].sum()))))
    scale = 100 if bnc and df[bnc].dropna().max() <= 1.5 else 1
    if bnc:
        rate = float(df[bnc].mean() * scale)
        F.append(("warn" if rate > 60 else "good", T("wb_bounce", lang, r=round(rate, 1), note=T("wb_hi" if rate > 60 else "wb_ok", lang))))
    skip = [c for c in (vis, bnc) if c]
    for g in _groups(df, kinds, ("page", "source", "device", "channel", "medium", "country", "browser"), 2, skip):
        if vis:
            tv = df.groupby(g)[vis].sum().sort_values(ascending=False)
            if len(tv) >= 2 and tv.sum() > 0:
                F.append(("info", T("wb_top", lang, col=g, g=str(tv.index[0]), p=round(float(tv.iloc[0] / tv.sum() * 100)))))
                A.append(T("a_source", lang, g=str(tv.index[0]), col=g))
        if bnc:
            bg = (df.groupby(g)[bnc].mean() * scale).dropna().sort_values(ascending=False)
            if len(bg) >= 2:
                F.append(("warn", T("wb_worst", lang, col=g, g=str(bg.index[0]), r=round(float(bg.iloc[0]), 1))))
                A.append(T("a_bounce", lang, g=str(bg.index[0]), col=g))
    return F, A, []


def _agriculture(df, kinds, lang):
    F, A = [], []
    y = _find(df, kinds, ("yield", "harvest", "production", "output"))
    if y:
        for g in _groups(df, kinds, ("crop", "plant", "field", "variety", "season", "farm"), 1, [y]):
            r = _best_worst(df.groupby(g)[y].mean())
            if r:
                F.append(("info", T("ag_crop", lang, col=g, b=str(r[0]), x=fmt(r[1]), y=y, w=str(r[2]), z=fmt(r[3]))))
                A.append(T("a_cropbest", lang, b=str(r[0])))
        drivers = [c for c in df.columns if kinds[c] == "number" and c != y and any(w in _key(c) for w in
                   ("rain", "water", "irrigation", "fertil", "temperature", "temp", "humidity", "moisture", "ph", "sun", "area", "acre"))]
        pairs = sorted(((abs(df[y].corr(df[c])), c, df[y].corr(df[c])) for c in drivers if pd.notna(df[y].corr(df[c]))), reverse=True)
        for _, c, r in pairs[:2]:
            if abs(r) >= 0.4:
                F.append(("info", T("ag_corr" if r > 0 else "ag_corr_neg", lang, y=y, x=c, r=round(float(r), 2))))
        for _, c, r in pairs:
            if r >= 0.4 and any(w in _key(c) for w in ("rain", "water", "irrigation", "moisture")):
                lo = df[c].quantile(1 / 3)
                a, b = df.loc[df[c] <= lo, y].mean(), df.loc[df[c] > lo, y].mean()
                if b and a < b:
                    F.append(("warn", T("ag_irrig", lang, y=y, x=c, p=round(float((b - a) / b * 100)))))
                break
    for c in df.columns:
        if kinds[c] == "category" and any(w in _key(c) for w in ("pest", "disease")):
            vc = df[c].value_counts(normalize=True)
            vc = vc[~vc.index.astype(str).str.lower().isin({"none", "no", "nil", "na", "n/a", "-"})]
            if len(vc):
                F.append(("warn", T("ag_pest", lang, col=c, g=str(vc.index[0]), p=round(float(vc.iloc[0] * 100)))))
                A.append(T("a_pest", lang, g=str(vc.index[0])))
            break
    return F, A, []


def _healthcare2(df, kinds, lang):
    F, A, TB = _healthcare(df, kinds, lang)
    out = next((c for c in df.columns if kinds[c] == "category" and any(w in _key(c) for w in ("outcome", "recover", "result", "status"))), None)
    tr = next((c for c in df.columns if kinds[c] == "category" and any(w in _key(c) for w in ("treatment", "medicine", "therapy", "drug"))), None)
    if out and tr:
        ok = df[out].astype(str).str.lower().str.contains("recover|cured|improv|success|discharg|better|yes")
        rate = (ok.groupby(df[tr]).mean() * 100).dropna().sort_values(ascending=False)
        if len(rate) >= 2:
            F.append(("info", T("p_eff", lang, col=tr, b=str(rate.index[0]), x=round(float(rate.iloc[0])), w=str(rate.index[-1]), y=round(float(rate.iloc[-1])))))
    return F, A, TB


def _logistics2(df, kinds, lang):
    F, A, TB = _logistics(df, kinds, lang)
    tm = _find(df, kinds, ("time", "duration", "minutes", "hours"), exclude=("date",))
    fuel = _find(df, kinds, ("fuel", "litre", "liter"))
    dist = _find(df, kinds, ("distance", "km", "mile"))
    for g in _groups(df, kinds, ("route", "vehicle", "driver", "zone"), 1, [c for c in (tm, fuel, dist) if c]):
        if tm:
            r = _best_worst(-df.groupby(g)[tm].mean())
            if r:
                F.append(("info", T("tr_time", lang, col=g, b=str(r[0]), x=fmt(-r[1]), w=str(r[2]), y=fmt(-r[3]))))
                A.append(T("a_route", lang, b=str(r[0]), col=g))
        if fuel and dist:
            ag = df.groupby(g)[[fuel, dist]].sum()
            eff = (ag[fuel] / ag[dist].replace(0, np.nan)).dropna()
            r = _best_worst(-eff)
            if r:
                F.append(("info", T("tr_fuel", lang, col=g, b=str(r[0]), w=str(r[2]))))
    return F, A, TB


RUN.update({"sales": _sales, "customers": _customers, "ecommerce": _ecommerce, "marketing": _marketing,
            "social": _social, "website": _website, "agriculture": _agriculture,
            "healthcare": _healthcare2, "logistics": _logistics2})

# a logistics file with no late/delay column used to return nothing: allow the route / fuel analysis to run
_orig_logistics = _logistics


def _logistics(df, kinds, lang):          # noqa: F811  (late part is optional)
    try:
        return _orig_logistics(df, kinds, lang)
    except Exception:
        return [], [], []


def detect(df):                           # noqa: F811  (more types, specific types win ties)
    keys = [_key(c) for c in df.columns]
    scores = {ind: sum(any(w in k for w in ws) for k in keys) for ind, ws in WORDS.items()}
    order = ["education", "agriculture", "manufacturing", "healthcare", "company", "social", "website", "marketing",
             "ecommerce", "logistics", "finance", "customers", "sales"]
    best = max(order, key=lambda i: (scores[i], -order.index(i)))
    return best if scores[best] >= 2 else None


# =================================================================== types 11-20 (inventory, banking, telecom, ...)
WORDS.update({
    "inventory": ("stock", "inventory", "reorder", "shortage", "availability", "warehouse", "onhand", "supplier", "demand", "sku"),
    "banking": ("loan", "repayment", "fraud", "credit", "emi", "overdue", "cibil", "account", "transaction", "default", "npa"),
    "telecom": ("call", "duration", "network", "churn", "plan", "recharge", "tower", "signal", "minutes", "roaming", "data usage"),
    "realestate": ("property", "rent", "sqft", "bhk", "bedroom", "locality", "plot", "floor", "builder", "carpet", "price"),
    "weather": ("temperature", "temp", "rainfall", "rain", "humidity", "wind", "pressure", "precipitation", "sunshine"),
    "product": ("rating", "quality", "defect", "complaint", "warranty", "demand", "model", "brand", "review"),
    "government": ("population", "census", "unemployment", "crime", "literacy", "district", "poverty", "households", "ward", "birth"),
})
WORDS["logistics"] = WORDS["logistics"] + ("shipping", "carrier", "accident", "supplychain")
WORDS["company"] = WORDS["company"] + ("attendance", "productivity", "performance")
LABEL["logistics"] = ("Supply chain / transport data", "விநியோக சங்கிலி / போக்குவரத்து தரவு")
LABEL.update({
    "inventory": ("Inventory data", "இருப்பு தரவு"), "banking": ("Banking data", "வங்கி தரவு"),
    "telecom": ("Telecom data", "தொலைத்தொடர்பு தரவு"), "realestate": ("Real estate data", "ரியல் எஸ்டேட் தரவு"),
    "weather": ("Weather data", "வானிலை தரவு"), "product": ("Product data", "பொருள் தரவு"),
    "government": ("Government / public data", "அரசு / பொது தரவு"),
})
H.update({"item": ("Item", "பொருள்"), "stock": ("Stock", "இருப்பு"), "demand": ("Demand", "தேவை"), "gap": ("Gap", "பற்றாக்குறை"),
          "price": ("Average price", "சராசரி விலை"), "psf": ("Price per area", "பரப்புக்கான விலை"),
          "listings": ("Listings", "பட்டியல்கள்"), "rating": ("Average rating", "சராசரி மதிப்பீடு")})
WHAT = {"fraud": ("fraud", "மோசடி"), "default": ("default / overdue", "தவணை தவறல்"), "churn": ("churn", "வெளியேறல்"),
        "defect": ("defect", "குறைபாடு")}
TX.update({
    "w_rate": ("{p}% of records show {what}.", "{p}% பதிவுகளில் {what} உள்ளது."),
    "w_worst": ("In {col}, \"{g}\" has the highest {what} rate ({p}%).", "{col} பிரிவில் \"{g}\" அதிக {what} விகிதம் ({p}%)."),
    "a_review": ("Review \"{g}\" ({col}) first; it has the highest {what} rate.", "\"{g}\" ({col})-ஐ முதலில் ஆய்வு செய்யுங்கள்; அதில் {what} விகிதம் அதிகம்."),
    # inventory
    "i_out": ("{n} items are out of stock.", "{n} பொருட்கள் கையிருப்பில் இல்லை."),
    "i_low": ("{n} items are at or below their reorder level.", "{n} பொருட்கள் மறுஆர்டர் அளவில் அல்லது அதற்குக் கீழ் உள்ளன."),
    "i_short": ("{n} items have less stock than demand: risk of running out.", "{n} பொருட்களில் தேவையை விட இருப்பு குறைவு: தீர்ந்துபோகும் அபாயம்."),
    "i_over": ("{n} items have more than 3 times the stock they need. Money is stuck there.", "{n} பொருட்களில் தேவையை விட 3 மடங்குக்கு மேல் இருப்பு உள்ளது. பணம் முடங்கியுள்ளது."),
    "a_order": ("Order the short items first (see the table).", "பற்றாக்குறை பொருட்களை முதலில் ஆர்டர் செய்யுங்கள் (அட்டவணையைப் பாருங்கள்)."),
    "a_overstock": ("Stop buying overstocked items and run an offer to clear them.", "அதிக இருப்புள்ள பொருட்களை வாங்குவதை நிறுத்தி, சலுகை மூலம் விற்றுத் தீருங்கள்."),
    "t_short": ("Items that may run out", "தீர்ந்துபோகக்கூடிய பொருட்கள்"),
    # banking
    "b_total": ("{n} transactions worth {v} in total, average {a}.", "{n} பரிவர்த்தனைகள், மொத்தம் {v}, சராசரி {a}."),
    "b_score": ("Average credit score is {a}. {p}% of customers score below 600 (higher risk).", "சராசரி கடன் மதிப்பெண் {a}. {p}% வாடிக்கையாளர்கள் 600-க்கு கீழ் (அதிக ஆபத்து)."),
    "a_fraud": ("Add an extra check for the flagged transactions before approving them.", "குறிக்கப்பட்ட பரிவர்த்தனைகளை அனுமதிக்கும் முன் கூடுதல் சரிபார்ப்பு செய்யுங்கள்."),
    "a_overdue": ("Call customers with overdue loans this week and offer a repayment plan.", "தவணை தவறிய வாடிக்கையாளர்களை இந்த வாரம் அழைத்து திருப்பிச் செலுத்தும் திட்டம் வழங்குங்கள்."),
    # telecom
    "tc_dur": ("Average call length is {a}; the longest is {m}.", "சராசரி அழைப்பு நேரம் {a}; அதிகபட்சம் {m}."),
    "tc_data": ("Average data use is {a}. The heaviest users are on \"{g}\" ({col}).", "சராசரி தரவு பயன்பாடு {a}. அதிகம் பயன்படுத்துவோர் \"{g}\" ({col}) பிரிவில் உள்ளனர்."),
    "tc_sig": ("In {col}, \"{g}\" has the weakest network quality (average {a}).", "{col} பிரிவில் \"{g}\" நெட்வொர்க் தரம் மிகக் குறைவு (சராசரி {a})."),
    "a_churn": ("Offer a better plan or a call to customers in \"{g}\" ({col}) before they leave.", "\"{g}\" ({col}) வாடிக்கையாளர்கள் வெளியேறும் முன் சிறந்த திட்டம் அல்லது அழைப்பு வழங்குங்கள்."),
    "a_net": ("Fix the network in \"{g}\" ({col}).", "\"{g}\" ({col})-இல் நெட்வொர்க்கை சரிசெய்யுங்கள்."),
    # real estate
    "r_avg": ("Average {col} is {a} (lowest {l}, highest {h}).", "சராசரி {col} {a} (குறைவு {l}, அதிகம் {h})."),
    "r_loc": ("In {col}, \"{g}\" is the most expensive (average {a}); \"{l}\" is the cheapest ({b}).", "{col} பிரிவில் \"{g}\" மிக அதிக விலை (சராசரி {a}); \"{l}\" மிகக் குறைவு ({b})."),
    "r_psf": ("Per {area}, \"{g}\" costs the most ({a}) and \"{l}\" the least ({b}).", "{area} அடிப்படையில் \"{g}\" அதிக விலை ({a}); \"{l}\" குறைவு ({b})."),
    "r_demand": ("\"{g}\" has the most listings ({p}% of all), so demand is highest there.", "\"{g}\" பகுதியில் அதிக பட்டியல்கள் ({p}%), எனவே தேவை அங்கு அதிகம்."),
    "r_bhk": ("Most common size: {g} ({p}%).", "அதிகம் காணப்படும் அளவு: {g} ({p}%)."),
    "a_area": ("Buyers pay the most in \"{g}\"; price new listings there carefully.", "வாங்குவோர் \"{g}\" பகுதியில் அதிகம் செலுத்துகின்றனர்; அங்கு புதிய பட்டியல்களை கவனமாக விலை நிர்ணயம் செய்யுங்கள்."),
    # weather
    "wx_temp": ("Temperature: average {a}, hottest {h}, coldest {c}.", "வெப்பநிலை: சராசரி {a}, அதிகபட்சம் {h}, குறைந்தபட்சம் {c}."),
    "wx_hot": ("{p} is the hottest period (average {a}); {q} is the coolest ({b}).", "{p} மிகவும் வெப்பமான காலம் (சராசரி {a}); {q} குளிர்ந்த காலம் ({b})."),
    "wx_rain": ("Total {col}: {t}. It rained on {n} records ({p}%).", "மொத்த {col}: {t}. {n} பதிவுகளில் மழை பெய்தது ({p}%)."),
    "wx_wet": ("{p} is the wettest period ({v}); {q} is the driest ({w}).", "{p} மிக ஈரமான காலம் ({v}); {q} மிக வறண்ட காலம் ({w})."),
    "wx_oth": ("Average {col} is {a} (highest {h}).", "சராசரி {col} {a} (அதிகம் {h})."),
    "a_dry": ("Plan watering and outdoor work around the dry period ({q}) and the wet period ({p}).", "வறண்ட காலம் ({q}) மற்றும் மழைக்காலம் ({p}) ஆகியவற்றை மையமாக வைத்து நீர்ப்பாசனம் மற்றும் வெளிப்புற வேலைகளைத் திட்டமிடுங்கள்."),
    # product
    "pr_rate": ("In {col}, \"{b}\" has the best rating ({x}); \"{w}\" has the worst ({y}).", "{col} பிரிவில் \"{b}\" சிறந்த மதிப்பீடு ({x}); \"{w}\" மிகக் குறைவு ({y})."),
    "pr_dem": ("\"{g}\" has the highest {m}.", "\"{g}\"-க்கு {m} அதிகம்."),
    "a_improve": ("Improve or replace \"{w}\" ({col}); customers rate it lowest.", "\"{w}\" ({col})-ஐ மேம்படுத்துங்கள் அல்லது மாற்றுங்கள்; வாடிக்கையாளர்கள் குறைவாக மதிப்பிடுகின்றனர்."),
    # government
    "pr_def": ("In {col}, \"{g}\" has the most defects or complaints ({n} in total).", "{col} பிரிவில் \"{g}\"-இல் குறைபாடுகள் அல்லது புகார்கள் அதிகம் (மொத்தம் {n})."),
    "g_pop": ("Total {col}: {t}. Largest: \"{a}\" ({x}); smallest: \"{b}\" ({y}).", "மொத்த {col}: {t}. பெரியது: \"{a}\" ({x}); சிறியது: \"{b}\" ({y})."),
    "g_high": ("Highest {col} is in \"{g}\" ({v}); lowest is in \"{l}\" ({w}).", "{col} அதிகம் உள்ளது \"{g}\"-இல் ({v}); குறைவு \"{l}\"-இல் ({w})."),
    "g_rate": ("Per 1,000 people, \"{g}\" has the highest {col} ({v}).", "1,000 பேருக்கு \"{g}\"-இல் {col} அதிகம் ({v})."),
    "a_focus": ("Focus help and funds on \"{g}\" ({col}); the need is highest there.", "\"{g}\" ({col})-இல் உதவியும் நிதியும் அதிகம் செலுத்துங்கள்; அங்கு தேவை அதிகம்."),
    # staff extras / transport extras
    "h_att": ("Average attendance is {a}%. {n} people are below 75%.", "சராசரி வருகை {a}%. {n} பேர் 75%-க்கும் குறைவு."),
    "h_attdept": ("In {col}, \"{g}\" has the lowest attendance ({a}%).", "{col} பிரிவில் \"{g}\" வருகை மிகக் குறைவு ({a}%)."),
    "h_prod": ("In {col}, \"{g}\" has the best {m} ({a}); \"{l}\" the lowest ({b}).", "{col} பிரிவில் \"{g}\" சிறந்த {m} ({a}); \"{l}\" குறைவு ({b})."),
    "tr_acc": ("Total accidents: {n}. Most are on {col} \"{g}\".", "மொத்த விபத்துகள்: {n}. அதிகம் {col} \"{g}\"-இல்."),
    "a_acc": ("Review safety on \"{g}\" ({col}): training, speed limits, vehicle checks.", "\"{g}\" ({col})-இல் பாதுகாப்பை ஆய்வு செய்யுங்கள்: பயிற்சி, வேக வரம்பு, வாகன சோதனை."),
})


def W(key, lang):
    return WHAT[key][1 if lang == "ta" else 0]


def _flag(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0) > 0
    v = series.astype(str).str.strip().str.lower()
    return v.isin({"yes", "y", "1", "true", "fraud", "fraudulent", "churned", "churn", "left", "default", "defaulted",
                   "overdue", "late", "npa", "suspicious", "flagged", "defective"}) | v.str.contains("fraud|default|overdue|churn|npa")


def _flag_col(df, kinds, words, want=("category", "number")):
    return next((c for c in df.columns if kinds[c] in want and any(w in _key(c) for w in words)), None)


def _rate_groups(df, kinds, mask, what, gwords, skip, lang, limit=1):
    F, A = [], []
    for g in _groups(df, kinds, gwords, limit, skip):
        gp = mask.groupby(df[g]).mean().sort_values(ascending=False) * 100
        if len(gp) >= 2 and gp.iloc[0] > 0:
            F.append(("warn", T("w_worst", lang, col=g, g=str(gp.index[0]), p=round(float(gp.iloc[0]), 1), what=W(what, lang))))
            A.append(T("a_review", lang, g=str(gp.index[0]), col=g, what=W(what, lang)))
    return F, A


def _inventory(df, kinds, lang):
    F, A, TB = [], [], []
    stock = _find(df, kinds, ("stock", "inventory", "onhand", "available", "quantity", "qty"), exclude=("reorder", "min", "demand", "sold"))
    reorder = _find(df, kinds, ("reorder", "minimum", "min", "safety"))
    demand = _find(df, kinds, ("demand", "sold", "sales", "consumption", "usage"))
    if not stock:
        return F, A, TB
    n_out = int((df[stock] <= 0).sum())
    if n_out:
        F.append(("warn", T("i_out", lang, n=n_out)))
    if reorder:
        low = (df[stock] <= df[reorder]) & (df[stock] > 0)
        if low.sum():
            F.append(("warn", T("i_low", lang, n=int(low.sum()))))
    if demand:
        short = df[stock] < df[demand]
        over = (df[demand] > 0) & (df[stock] > 3 * df[demand])
        if short.sum():
            F.append(("warn", T("i_short", lang, n=int(short.sum()))))
            A.append(T("a_order", lang))
            nm = _name_col(df, kinds) or next((c for c in df.columns if kinds[c] in ("id", "text", "category")), None)
            if nm:
                gap = (df[demand] - df[stock]).where(short).dropna().sort_values(ascending=False).head(8)
                TB.append({"title": T("t_short", lang), "cols": [Hd("item", lang), Hd("stock", lang), Hd("demand", lang), Hd("gap", lang)],
                           "rows": _rows([[str(df.loc[i, nm]), df.loc[i, stock], df.loc[i, demand], gap[i]] for i in gap.index])})
        if over.sum():
            F.append(("info", T("i_over", lang, n=int(over.sum()))))
            A.append(T("a_overstock", lang))
    return F, A, TB


def _banking(df, kinds, lang):
    F, A = [], []
    amt = _find(df, kinds, ("amount", "value", "transaction"), exclude=("loan", "score"))
    if amt:
        v = df[amt].dropna()
        F.append(("info", T("b_total", lang, n=f"{len(v):,}", v=fmt(v.sum()), a=fmt(v.mean()))))
    fr = _flag_col(df, kinds, ("fraud", "suspicious", "flag"))
    if fr:
        m = _flag(df[fr])
        if m.sum():
            F.append(("warn", T("w_rate", lang, p=round(float(m.mean() * 100), 2), what=W("fraud", lang))))
            f2, a2 = _rate_groups(df, kinds, m, "fraud", ("channel", "type", "merchant", "city", "mode", "branch"), [fr], lang)
            F += f2; A += a2 + [T("a_fraud", lang)]
    df_c = _flag_col(df, kinds, ("default", "overdue", "npa", "repayment", "status"), want=("category", "number"))
    if df_c and df_c != fr:
        m = _flag(df[df_c])
        if m.sum():
            F.append(("warn" if m.mean() > 0.05 else "info", T("w_rate", lang, p=round(float(m.mean() * 100), 2), what=W("default", lang))))
            f2, a2 = _rate_groups(df, kinds, m, "default", ("loan", "type", "branch", "city", "product", "occupation"), [df_c], lang)
            F += f2; A += a2 + [T("a_overdue", lang)]
    sc = _find(df, kinds, ("cibil", "creditscore", "score"))
    if sc:
        v = df[sc].dropna()
        if len(v) and v.between(250, 950).mean() > 0.9:
            F.append(("warn" if (v < 600).mean() > 0.2 else "info", T("b_score", lang, a=fmt(v.mean()), p=round(float((v < 600).mean() * 100)))))
    return F, A, []


def _telecom(df, kinds, lang):
    F, A = [], []
    ch = _flag_col(df, kinds, ("churn",))
    if ch:
        m = _flag(df[ch])
        if m.sum():
            F.append(("warn" if m.mean() > 0.15 else "info", T("w_rate", lang, p=round(float(m.mean() * 100), 1), what=W("churn", lang))))
            f2, a2 = _rate_groups(df, kinds, m, "churn", ("plan", "contract", "region", "circle", "city", "tower", "device"), [ch], lang)
            F += f2
            for g in _groups(df, kinds, ("plan", "contract", "region", "circle", "city"), 1, [ch]):
                gp = (m.groupby(df[g]).mean() * 100).sort_values(ascending=False)
                if len(gp) >= 2 and gp.iloc[0] > 0:
                    A.append(T("a_churn", lang, g=str(gp.index[0]), col=g))
    dur = _find(df, kinds, ("duration", "minutes", "calllength"))
    if dur:
        F.append(("info", T("tc_dur", lang, a=fmt(df[dur].mean()), m=fmt(df[dur].max()))))
    dat = _find(df, kinds, ("datausage", "data", "gb", "mb"), exclude=("date", "plan"))
    if dat:
        for g in _groups(df, kinds, ("plan", "package", "region", "device"), 1, [dat]):
            gs = df.groupby(g)[dat].mean().sort_values(ascending=False)
            if len(gs) >= 2:
                F.append(("info", T("tc_data", lang, a=fmt(df[dat].mean()), g=str(gs.index[0]), col=g)))
    sig = _find(df, kinds, ("signal", "quality", "strength", "speed", "latency"), exclude=("churn",))
    if sig:
        for g in _groups(df, kinds, ("tower", "region", "circle", "area", "city"), 1, [sig]):
            gs = df.groupby(g)[sig].mean().dropna().sort_values()
            if len(gs) >= 2:
                F.append(("warn", T("tc_sig", lang, col=g, g=str(gs.index[0]), a=fmt(gs.iloc[0]))))
                A.append(T("a_net", lang, g=str(gs.index[0]), col=g))
    return F, A, []


def _realestate(df, kinds, lang):
    F, A, TB = [], [], []
    price = _find(df, kinds, ("price", "rent", "cost", "value"), exclude=("persqft", "per"))
    area = _find(df, kinds, ("sqft", "area", "size", "carpet"), exclude=("price",))
    if not price:
        return F, A, TB
    v = df[price].dropna()
    F.append(("info", T("r_avg", lang, col=price, a=fmt(v.mean()), l=fmt(v.min()), h=fmt(v.max()))))
    for g in _groups(df, kinds, ("location", "locality", "area", "city", "zone", "neighbourhood", "neighborhood", "place"), 1, [c for c in (price, area) if c]):
        gm = df.groupby(g)[price].mean().dropna().sort_values(ascending=False)
        if len(gm) >= 2:
            F.append(("info", T("r_loc", lang, col=g, g=str(gm.index[0]), a=fmt(gm.iloc[0]), l=str(gm.index[-1]), b=fmt(gm.iloc[-1]))))
            A.append(T("a_area", lang, g=str(gm.index[0])))
        vc = df[g].value_counts(normalize=True)
        F.append(("info", T("r_demand", lang, g=str(vc.index[0]), p=round(float(vc.iloc[0] * 100)))))
        rows = [[str(i), int((df[g] == i).sum()), round(float(gm[i]))] for i in gm.index]
        if area:
            psf = (df.groupby(g)[price].sum() / df.groupby(g)[area].sum().replace(0, np.nan)).dropna().sort_values(ascending=False)
            if len(psf) >= 2:
                F.append(("info", T("r_psf", lang, area=area, g=str(psf.index[0]), a=fmt(psf.iloc[0]), l=str(psf.index[-1]), b=fmt(psf.iloc[-1]))))
        TB.append({"title": g, "cols": [g, Hd("listings", lang), Hd("price", lang)], "rows": _rows(rows)})
    for c in df.columns:
        if any(w in _key(c) for w in ("bhk", "bedroom", "type")) and kinds[c] in ("category", "number") and df[c].nunique() <= 12:
            vc = df[c].value_counts(normalize=True)
            F.append(("info", T("r_bhk", lang, g=str(vc.index[0]), p=round(float(vc.iloc[0] * 100)))))
            break
    return F, A, TB


def _weather(df, kinds, lang):
    from datareport import _period_keys
    F, A = [], []
    temp = _find(df, kinds, ("temperature", "temp"))
    rain = _find(df, kinds, ("rain", "precip"))
    pk = _period_keys(df, kinds)
    if temp:
        v = df[temp].dropna()
        F.append(("info", T("wx_temp", lang, a=fmt(v.mean()), h=fmt(v.max()), c=fmt(v.min()))))
        if pk is not None:
            tp = df.groupby(pk[0])[temp].mean().dropna()
            if len(tp) >= 2:
                F.append(("info", T("wx_hot", lang, p=pk[1](tp.idxmax()), a=fmt(tp.max()), q=pk[1](tp.idxmin()), b=fmt(tp.min()))))
    if rain:
        v = df[rain].dropna()
        wet = int((v > 0).sum())
        F.append(("info", T("wx_rain", lang, col=rain, t=fmt(v.sum()), n=wet, p=round(wet / max(len(v), 1) * 100))))
        if pk is not None:
            rp = df.groupby(pk[0])[rain].sum().dropna()
            if len(rp) >= 2 and rp.max() > 0:
                F.append(("info", T("wx_wet", lang, p=pk[1](rp.idxmax()), v=fmt(rp.max()), q=pk[1](rp.idxmin()), w=fmt(rp.min()))))
                A.append(T("a_dry", lang, p=pk[1](rp.idxmax()), q=pk[1](rp.idxmin())))
    for words in (("humidity",), ("wind",), ("pressure",)):
        c = _find(df, kinds, words)
        if c:
            F.append(("info", T("wx_oth", lang, col=c, a=fmt(df[c].mean()), h=fmt(df[c].max()))))
    return F, A, []


def _product(df, kinds, lang):
    F, A = [], []
    rate = _find(df, kinds, ("rating", "review", "quality", "satisfaction"))
    dem = _find(df, kinds, ("demand", "sold", "orders", "units"))
    defect = _find(df, kinds, ("defect", "complaint", "fault"))
    for g in _groups(df, kinds, ("product", "model", "brand", "item", "category"), 1, [c for c in (rate, dem, defect) if c]):
        if rate:
            r = _best_worst(df.groupby(g)[rate].mean())
            if r:
                F.append(("info", T("pr_rate", lang, col=g, b=str(r[0]), x=fmt(r[1]), w=str(r[2]), y=fmt(r[3]))))
                A.append(T("a_improve", lang, w=str(r[2]), col=g))
        if dem:
            d = df.groupby(g)[dem].sum().sort_values(ascending=False)
            if len(d) >= 2:
                F.append(("info", T("pr_dem", lang, g=str(d.index[0]), m=dem)))
        if defect:
            r = _best_worst(df.groupby(g)[defect].sum())
            if r and r[1] > 0:
                F.append(("warn", T("pr_def", lang, col=g, g=str(r[0]), n=fmt(r[1]))))
    if rate and dem and df[rate].corr(df[dem]) >= 0.4:
        F.append(("info", T("ag_corr", lang, y=dem, x=rate, r=round(float(df[rate].corr(df[dem])), 2))))
    return F, A, []


def _government(df, kinds, lang):
    F, A = [], []
    pop = _find(df, kinds, ("population", "people", "households", "residents"))
    gcols = _groups(df, kinds, ("district", "state", "ward", "taluk", "block", "village", "city", "area", "region"), 1, [pop] if pop else [])
    if not gcols:
        nm = next((c for c in df.columns if kinds[c] in ("id", "text") and df[c].nunique() == len(df)), None)
        gcols = [nm] if nm else []
    if not gcols:
        return F, A, []
    g = gcols[0]
    if pop:
        ps = df.groupby(g)[pop].sum().sort_values(ascending=False)
        if len(ps) >= 2:
            F.append(("info", T("g_pop", lang, col=pop, t=fmt(ps.sum()), a=str(ps.index[0]), x=fmt(ps.iloc[0]), b=str(ps.index[-1]), y=fmt(ps.iloc[-1]))))
    for words, higher_bad in ((("unemploy",), True), (("poverty",), True), (("crime",), True), (("literacy",), False), (("birth", "death"), None)):
        c = _find(df, kinds, words, exclude=("rate_",) if False else ())
        if not c or c == pop:
            continue
        agg = df.groupby(g)[c].mean() if "rate" in _key(c) or "percent" in _key(c) or "pct" in _key(c) else df.groupby(g)[c].sum()
        agg = agg.dropna().sort_values(ascending=False)
        if len(agg) >= 2:
            F.append(("info", T("g_high", lang, col=c, g=str(agg.index[0]), v=fmt(agg.iloc[0]), l=str(agg.index[-1]), w=fmt(agg.iloc[-1]))))
            if pop and "rate" not in _key(c) and "percent" not in _key(c) and higher_bad:
                per = (df.groupby(g)[c].sum() / df.groupby(g)[pop].sum().replace(0, np.nan) * 1000).dropna().sort_values(ascending=False)
                if len(per) >= 2:
                    F.append(("warn", T("g_rate", lang, col=c, g=str(per.index[0]), v=fmt(per.iloc[0]))))
                    A.append(T("a_focus", lang, g=str(per.index[0]), col=c))
            elif higher_bad:
                A.append(T("a_focus", lang, g=str(agg.index[0]), col=c))
            elif higher_bad is False:
                A.append(T("a_focus", lang, g=str(agg.index[-1]), col=c))
    return F, A, []


_company_base = _company


def _company2(df, kinds, lang):
    F, A, TB = _company_base(df, kinds, lang)
    att = _find(df, kinds, ("attendance", "present"))
    prod = _find(df, kinds, ("productivity", "performance", "target", "tasks", "rating"))
    if att:
        v = df[att].dropna()
        if len(v) and v.max() <= 100:
            F.append(("info", T("h_att", lang, a=fmt(v.mean()), n=int((v < 75).sum()))))
            for g in _groups(df, kinds, ("department", "dept", "team", "branch", "location"), 1, [att]):
                gm = df.groupby(g)[att].mean().dropna().sort_values()
                if len(gm) >= 2:
                    F.append(("warn", T("h_attdept", lang, col=g, g=str(gm.index[0]), a=fmt(gm.iloc[0]))))
    if prod:
        for g in _groups(df, kinds, ("department", "dept", "team", "branch", "location"), 1, [c for c in (att, prod) if c]):
            r = _best_worst(df.groupby(g)[prod].mean())
            if r:
                F.append(("info", T("h_prod", lang, col=g, g=str(r[0]), m=prod, a=fmt(r[1]), l=str(r[2]), b=fmt(r[3]))))
    return F, A, TB


_logistics2_base = _logistics2


def _logistics3(df, kinds, lang):
    F, A, TB = _logistics2_base(df, kinds, lang)
    acc = _find(df, kinds, ("accident", "incident", "crash"))
    if acc:
        for g in _groups(df, kinds, ("route", "vehicle", "driver", "zone", "road"), 1, [acc]):
            gs = df.groupby(g)[acc].sum().sort_values(ascending=False)
            if len(gs) >= 2 and gs.iloc[0] > 0:
                F.append(("warn", T("tr_acc", lang, n=fmt(df[acc].sum()), col=g, g=str(gs.index[0]))))
                A.append(T("a_acc", lang, g=str(gs.index[0]), col=g))
    return F, A, TB


RUN.update({"inventory": _inventory, "banking": _banking, "telecom": _telecom, "realestate": _realestate,
            "weather": _weather, "product": _product, "government": _government,
            "company": _company2, "logistics": _logistics3})


def detect(df):                           # noqa: F811  (final version: all 20 types)
    keys = [_key(c) for c in df.columns]
    scores = {ind: sum(any(w in k for w in ws) for k in keys) for ind, ws in WORDS.items()}
    order = ["education", "agriculture", "weather", "manufacturing", "healthcare", "banking", "telecom", "realestate",
             "government", "company", "social", "website", "marketing", "inventory", "ecommerce", "logistics",
             "finance", "product", "customers", "sales"]
    best = max(order, key=lambda i: (scores.get(i, 0), -order.index(i)))
    return best if scores.get(best, 0) >= 2 else None
