import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

REQUIRED_COLUMNS = ["InvoiceNo", "CustomerID", "Quantity", "UnitPrice", "InvoiceDate"]


def load_data(path):
    if path.lower().endswith(".xlsx"):
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="ISO-8859-1")


def clean_data(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))
    df = df.dropna(subset=["CustomerID"])
    df = df.drop_duplicates()
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    return df


def build_rfm(df):
    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    return df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
    )


def scale_rfm(rfm):
    transformed = rfm.copy()
    transformed["Frequency"] = transformed["Frequency"] ** 0.5
    transformed["Monetary"] = transformed["Monetary"] ** 0.5
    return StandardScaler().fit_transform(transformed)


def find_best_k(X, k_range=range(2, 9)):
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        scores[k] = silhouette_score(X, km.labels_)
    return max(scores, key=scores.get)


def name_segments(rfm):
    summary = rfm.groupby("Cluster").agg(
        Recency=("Recency", "mean"),
        Frequency=("Frequency", "mean"),
        Monetary=("Monetary", "mean"),
        Customers=("Recency", "count"),
    ).round(1)

    names = {}
    for c, row in summary.iterrows():
        if row["Monetary"] >= summary["Monetary"].quantile(0.75) and row["Recency"] <= summary["Recency"].median():
            names[c] = "Champions (high spend, recent)"
        elif row["Recency"] >= summary["Recency"].quantile(0.75):
            names[c] = "At-risk / Lost (haven't bought recently)"
        elif row["Frequency"] >= summary["Frequency"].median():
            names[c] = "Loyal customers"
        else:
            names[c] = "Occasional buyers"
    summary["Segment"] = summary.index.map(names)
    return summary


def run_pipeline(path):
    df = clean_data(load_data(path))
    rfm = build_rfm(df)
    X = scale_rfm(rfm)
    k = find_best_k(X)

    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    rfm = rfm.copy()
    rfm["Cluster"] = km.labels_

    summary = name_segments(rfm)
    total = int(summary["Customers"].sum())
    summary["Share"] = (summary["Customers"] / total * 100).round(1)
    summary = summary.sort_values("Monetary", ascending=False)

    return {
        "rows": len(df),
        "customers": total,
        "k": k,
        "segments": summary.reset_index().to_dict("records"),
    }