import re
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Keep the free server fast: only the first MAX_ROWS rows are read.
MAX_ROWS = 150000

# Common column names that people use -> the name this app uses.
ALIASES = {
    "InvoiceNo": ["invoiceno", "invoice", "invoicenumber", "orderid", "orderno",
                  "ordernumber", "transactionid", "billno", "billnumber"],
    "CustomerID": ["customerid", "custid", "customerno", "clientid", "userid", "customer"],
    "Quantity": ["quantity", "qty", "units", "unitssold", "quantitysold"],
    "UnitPrice": ["unitprice", "price", "priceperunit", "sellingprice", "rate", "itemprice"],
    "InvoiceDate": ["invoicedate", "orderdate", "date", "transactiondate",
                    "purchasedate", "datetime", "saledate"],
    "Description": ["description", "product", "productname", "itemname", "item", "productdescription"],
    "StockCode": ["stockcode", "sku", "productid", "productcode", "itemcode", "itemid"],
    "Country": ["country", "region", "state", "city"],
    "Stock": ["stock", "stockinhand", "instock", "onhand", "inventory", "stockleft",
              "stockquantity", "currentstock"],
}
MUST_HAVE = ["Quantity", "UnitPrice", "InvoiceDate"]


def _key(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def load_data(path):
    """Read a CSV or Excel file (first MAX_ROWS rows only)."""
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path, nrows=MAX_ROWS + 1)
    else:
        try:
            df = pd.read_csv(path, nrows=MAX_ROWS + 1, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, nrows=MAX_ROWS + 1, encoding="ISO-8859-1")
    truncated = len(df) > MAX_ROWS
    return df.iloc[:MAX_ROWS].copy(), truncated


def standardise_columns(df):
    """Rename common column names to the ones the app uses."""
    rename, used = {}, set()
    by_key = {_key(c): c for c in df.columns}
    for target, names in ALIASES.items():
        for n in names:
            if n in by_key and by_key[n] not in used:
                rename[by_key[n]] = target
                used.add(by_key[n])
                break
    df = df.rename(columns=rename)
    missing = [c for c in MUST_HAVE if c not in df.columns]
    if missing:
        raise ValueError(
            "These columns are missing: " + ", ".join(missing) +
            ". Your file needs a quantity, a price and a date column "
            "(for example Quantity, UnitPrice, InvoiceDate).")
    return df


def clean_data(df):
    df = standardise_columns(df)
    df = df.drop_duplicates()
    if "InvoiceNo" in df.columns:
        df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    else:
        df["InvoiceNo"] = np.arange(len(df))
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["Quantity", "UnitPrice", "InvoiceDate"])
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    if df.empty:
        raise ValueError("No valid sales rows were found after cleaning the file.")
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    if "Description" in df.columns:
        df["Description"] = df["Description"].astype(str).str.strip()
    if "StockCode" in df.columns:
        df["StockCode"] = df["StockCode"].astype(str).str.strip()
    # one name per product
    if "Description" in df.columns:
        df["Product"] = df["Description"]
    elif "StockCode" in df.columns:
        df["Product"] = df["StockCode"]
    return df


def build_rfm(df):
    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    g = df.groupby("CustomerID")
    return pd.DataFrame({
        "Recency": (snapshot - g["InvoiceDate"].max()).dt.days,
        "Frequency": g["InvoiceNo"].nunique(),
        "Monetary": g["TotalPrice"].sum(),
    })


def scale_rfm(rfm):
    t = rfm.copy()
    t["Frequency"] = t["Frequency"] ** 0.5
    t["Monetary"] = t["Monetary"] ** 0.5
    return StandardScaler().fit_transform(t)


def find_best_k(X):
    top = min(8, len(X) - 1)
    best_k, best = 2, -1
    size = min(len(X), 5000)
    for k in range(2, top + 1):
        km = KMeans(n_clusters=k, n_init=5, random_state=42).fit(X)
        score = silhouette_score(X, km.labels_, sample_size=size, random_state=42)
        if score > best:
            best_k, best = k, score
    return best_k


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


def segment_customers(df):
    """Returns (result dict, per-customer DataFrame) or (None, None) if not possible."""
    if "CustomerID" not in df.columns:
        return None, None
    d = df.dropna(subset=["CustomerID"])
    rfm = build_rfm(d)
    if len(rfm) < 10:
        return None, None
    X = scale_rfm(rfm)
    k = find_best_k(X)
    km = KMeans(n_clusters=k, n_init=5, random_state=42).fit(X)
    rfm = rfm.copy()
    rfm["Cluster"] = km.labels_
    summary = name_segments(rfm)
    rfm["Segment"] = rfm["Cluster"].map(summary["Segment"])
    total = int(summary["Customers"].sum())
    summary["Share"] = (summary["Customers"] / total * 100).round(1)
    summary = summary.sort_values("Monetary", ascending=False)
    top = rfm.sort_values("Monetary", ascending=False).head(15).reset_index()
    top["Monetary"] = top["Monetary"].round(0)
    result = {
        "customers": total,
        "k": k,
        "segments": summary.reset_index().to_dict("records"),
        "top_customers": top[["CustomerID", "Segment", "Recency", "Frequency", "Monetary"]].to_dict("records"),
    }
    return result, rfm.reset_index().drop(columns=["Cluster"])
