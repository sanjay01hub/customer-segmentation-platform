import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

DATA_PATH = "data/online+retail/Online Retail.xlsx"


def load_data(path):
    if path.endswith(".xlsx"):
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="ISO-8859-1")


def clean_data(df):
    df = df.dropna(subset=["CustomerID"])
    df = df.drop_duplicates()
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    return df


def build_rfm(df):
    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
    )
    return rfm


def scale_rfm(rfm):
    transformed = rfm.copy()
    transformed["Frequency"] = transformed["Frequency"] ** 0.5
    transformed["Monetary"] = transformed["Monetary"] ** 0.5
    scaler = StandardScaler()
    return scaler.fit_transform(transformed), scaler


def find_best_k(X, k_range=range(2, 9)):
    inertias, scores = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        inertias.append(km.inertia_)
        scores.append(silhouette_score(X, km.labels_))

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(list(k_range), inertias, marker="o")
    ax[0].set(title="Elbow method", xlabel="k", ylabel="Inertia")
    ax[1].plot(list(k_range), scores, marker="o", color="green")
    ax[1].set(title="Silhouette score", xlabel="k", ylabel="Score")
    plt.tight_layout()
    plt.savefig("k_selection.png")
    plt.show()

    best_k = list(k_range)[scores.index(max(scores))]
    print(f"Best k by silhouette score: {best_k}")
    return best_k


def run_kmeans(X, rfm, k):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    rfm = rfm.copy()
    rfm["Cluster"] = km.labels_
    return rfm


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
    rfm["Segment"] = rfm["Cluster"].map(names)
    return summary, rfm


def plot_segments(rfm):
    counts = rfm["Segment"].value_counts()
    counts.plot(kind="bar", figsize=(8, 4), title="Customers per segment")
    plt.ylabel("Customers")
    plt.tight_layout()
    plt.savefig("segment_sizes.png")
    plt.show()


if __name__ == "__main__":
    df = clean_data(load_data(DATA_PATH))
    print("Rows after cleaning:", len(df))

    rfm = build_rfm(df)
    print(rfm.describe().round(1))

    X, _ = scale_rfm(rfm)
    k = find_best_k(X)
    rfm = run_kmeans(X, rfm, k)

    summary, rfm = name_segments(rfm)
    print("\nSegment summary:\n", summary)

    plot_segments(rfm)
    rfm.to_csv("rfm_segments.csv")
    print("\nSaved rfm_segments.csv")