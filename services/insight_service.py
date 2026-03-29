from datetime import datetime
import calendar
import pandas as pd
 
 
def get_additional_insights(df: pd.DataFrame) -> list:
    insights = []
    if df.empty:
        return insights
 
    category_spend = df.groupby("category")["amount"].sum()
    top_category = category_spend.idxmax()
    top_amount = int(category_spend.max())
 
    insights.append({
        "type": "warn",
        "message": (
            f"You are spending most on <strong>{top_category}</strong> "
            f"(&#8377;{top_amount:,}). Review if this aligns with your budget."
        ),
    })
 
    avg_spend = df["amount"].mean()
    high_spends = df[df["amount"] > avg_spend * 2]
    if not high_spends.empty:
        insights.append({
            "type": "alert",
            "message": (
                f"You have <strong>{len(high_spends)}</strong> unusually high "
                "expense(s) &mdash; more than 2&times; your average. Review them."
            ),
        })
 
    total = df["amount"].sum()
    if total > 8000:
        insights.append({
            "type": "warn",
            "message": (
                "Your total spending is relatively high. "
                "Try reducing non-essential expenses to boost savings."
            ),
        })
 
    if len(df) < 20:
        insights.append({
            "type": "good",
            "message": (
                f"Great discipline! Only <strong>{len(df)}</strong> transactions "
                "recorded &mdash; you&apos;re keeping a tight rein on spending."
            ),
        })
 
    days_remaining = (
        calendar.monthrange(datetime.today().year, datetime.today().month)[1]
        - datetime.today().day
    )
    if days_remaining > 0:
        projected_savings = 100 * days_remaining
        insights.append({
            "type": "tip",
            "message": (
                f"Cutting just <strong>&#8377;100/day</strong> for the remaining "
                f"{days_remaining} days saves you &#8377;{projected_savings:,} this month."
            ),
        })
 
    return insights
 
 
def get_summary(file_path: str) -> dict:
    """Read daily_spending.csv and return dashboard summary dict."""
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"[insight_service] Could not read CSV: {e}")
        return _empty()
 
    # Clean
    df = df.dropna(subset=["amount", "category"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df = df[df["amount"] > 0]
 
    if df.empty:
        return _empty()
 
    total_spent    = int(df["amount"].sum())
    category_spend = df.groupby("category")["amount"].sum()
    top_category   = category_spend.idxmax()
    avg_per_txn    = int(df["amount"].mean())
    num_txn        = len(df)
    insights       = get_additional_insights(df)
 
    return {
        "total_spent":        f"{total_spent:,}",
        "top_category":       top_category,
        "category_breakdown": {k: int(v) for k, v in category_spend.to_dict().items()},
        "avg_daily":          f"{avg_per_txn:,}",
        "num_transactions":   num_txn,
        "insights":           insights,
    }
 
 
def _empty() -> dict:
    return {
        "total_spent":        "0",
        "top_category":       "N/A",
        "category_breakdown": {},
        "avg_daily":          "0",
        "num_transactions":   0,
        "insights":           [],
    }