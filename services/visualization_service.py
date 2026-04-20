import pandas as pd
import os


def get_chart_data(data_dir: str) -> dict:
    """
    Returns chart-ready data structures for the frontend.
    """
    path = os.path.join(data_dir, "daily_spending.csv")
    if not os.path.exists(path):
        return {"labels": [], "datasets": [], "daily": {}}

    try:
        df = pd.read_csv(path)
        df = df.dropna(subset=["amount", "category"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        # Category totals for pie/bar chart
        cat_totals = df.groupby("category")["amount"].sum().to_dict()
        labels = list(cat_totals.keys())
        values = list(cat_totals.values())

        # Daily totals for line chart
        daily = {}
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            daily = {
                k: int(v) for k, v in sorted(
                    df.groupby(df["date"].dt.strftime("%Y-%m-%d"))["amount"].sum().items()
                )
            }

        return {
            "labels": labels,
            "values": values,
            "daily": daily
        }
    except Exception:
        return {"labels": [], "values": [], "daily": {}}
