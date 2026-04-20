import pandas as pd
from datetime import datetime


def get_summary(file_path: str) -> dict:
    """
    Reads the daily_spending CSV and returns a structured summary dict with:
    - total_spent
    - top_category
    - category_breakdown
    - avg_daily
    - num_transactions
    - insights (list of dicts with type/message)
    """
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["amount", "category"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    if df.empty:
        return {
            "total_spent": "0",
            "top_category": "N/A",
            "category_breakdown": {},
            "avg_daily": "0",
            "num_transactions": 0,
            "insights": []
        }

    total_spent = df["amount"].sum()
    category_breakdown = df.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
    top_category = max(category_breakdown, key=category_breakdown.get) if category_breakdown else "N/A"
    num_transactions = len(df)

    # Avg daily spend
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        unique_days = df["date"].nunique()
        avg_daily = round(total_spent / unique_days, 2) if unique_days > 0 else round(total_spent, 2)
    else:
        avg_daily = round(total_spent / num_transactions, 2) if num_transactions > 0 else 0

    # ── Insight generation ────────────────────────────────────────────────────
    insights = []

    LIMITS = {
        "Food & Dining": 7000,
        "Transport":     5000,
        "Shopping":      6000,
        "Utilities":     4000,
        "Entertainment": 3000,
        "Health":        3000,
        "Food":          7000,
    }
    DEFAULT_LIMIT = 5000

    for cat, spent in category_breakdown.items():
        limit = LIMITS.get(cat, DEFAULT_LIMIT)
        pct = (spent / limit) * 100

        if pct >= 100:
            insights.append({
                "type": "danger",
                "message": (
                    f"🚨 <strong>{cat}</strong> has exceeded its budget! "
                    f"Spent ₹{spent:,.0f} of ₹{limit:,} limit."
                )
            })
        elif pct >= 80:
            insights.append({
                "type": "warning",
                "message": (
                    f"⚠️ <strong>{cat}</strong> is nearing its limit — "
                    f"₹{spent:,.0f} of ₹{limit:,} used ({pct:.0f}%)."
                )
            })

    # Top spender insight
    top_amt = category_breakdown.get(top_category, 0)
    insights.append({
        "type": "info",
        "message": (
            f"📊 Your highest spending is in <strong>{top_category}</strong> "
            f"at ₹{top_amt:,.0f} this month."
        )
    })

    # Avg daily insight
    if avg_daily > 2000:
        insights.append({
            "type": "warning",
            "message": (
                f"📅 Your daily average spend is ₹{avg_daily:,.0f}. "
                f"Consider setting a daily limit of ₹1,500."
            )
        })
    else:
        insights.append({
            "type": "success",
            "message": (
                f"✅ Great job! Your daily average spend is ₹{avg_daily:,.0f} — "
                f"well within a healthy range."
            )
        })

    return {
        "total_spent": f"{total_spent:,.0f}",
        "top_category": top_category,
        "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
        "avg_daily": f"{avg_daily:,.0f}",
        "num_transactions": num_transactions,
        "insights": insights
    }