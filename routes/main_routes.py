import os
from datetime import datetime
from flask import Blueprint, render_template, current_app
from services.insight_service import get_summary
import pandas as pd

main_bp = Blueprint("main", __name__)

PALETTE = {
    "Food & Dining":  {"color": "#ff6b6b", "bg": "#fff0f0", "icon": "🍜", "limit": 7000},
    "Transport":      {"color": "#4f6ef7", "bg": "#eef1fe", "icon": "🚗", "limit": 5000},
    "Shopping":       {"color": "#9b5de5", "bg": "#f5eeff", "icon": "🛍️", "limit": 6000},
    "Utilities":      {"color": "#f5a623", "bg": "#fef6e7", "icon": "⚡", "limit": 4000},
    "Entertainment":  {"color": "#00c9a7", "bg": "#e6faf6", "icon": "🎬", "limit": 3000},
    "Health":         {"color": "#2d6a4f", "bg": "#eaf4ef", "icon": "💊", "limit": 3000},
    "Food":           {"color": "#ff6b6b", "bg": "#fff0f0", "icon": "🍜", "limit": 7000},
}
DEFAULT_P = {"color": "#4f6ef7", "bg": "#eef1fe", "icon": "📦", "limit": 5000}


def _now():
    return datetime.now().strftime("%B %Y")


def _load_df(data_dir):
    path = os.path.join(data_dir, "daily_spending.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["date", "amount", "category"])
    df = pd.read_csv(path)
    df = df.dropna(subset=["amount", "category"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df


def _empty_summary():
    return {
        "total_spent": "0",
        "top_category": "N/A",
        "category_breakdown": {},
        "avg_daily": "0",
        "num_transactions": 0,
        "insights": []
    }


def _get_summary_safe(data_dir):
    path = os.path.join(data_dir, "daily_spending.csv")
    if not os.path.exists(path):
        return _empty_summary()
    try:
        return get_summary(path)
    except Exception as e:
        current_app.logger.error("Summary error: %s", e)
        return _empty_summary()


@main_bp.route("/")
def dashboard():
    data_dir = current_app.config["DATA_DIR"]
    summary = _get_summary_safe(data_dir)
    return render_template("dashboard.html", summary=summary, now=_now(), active_page="overview")


@main_bp.route("/analytics")
def analytics():
    data_dir = current_app.config["DATA_DIR"]
    df = _load_df(data_dir)
    summary = _get_summary_safe(data_dir)
    daily_totals = {}
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        daily_totals = {
            k: int(v) for k, v in sorted(
                df.groupby(df["date"].dt.strftime("%Y-%m-%d"))["amount"].sum().to_dict().items()
            )
        }
    return render_template("analytics.html", summary=summary, daily_totals=daily_totals, now=_now(), active_page="analytics")


@main_bp.route("/transactions")
def transactions():
    data_dir = current_app.config["DATA_DIR"]
    df = _load_df(data_dir)
    summary = _get_summary_safe(data_dir)
    txn_list = []
    if not df.empty:
        for _, row in df.sort_values("date", ascending=False).iterrows():
            cat = str(row.get("category", "Other"))
            p = PALETTE.get(cat, DEFAULT_P)
            txn_list.append({
                "date": str(row.get("date", "")),
                "category": cat,
                "amount": float(row["amount"]),
                "color": p["color"],
                "bg": p["bg"],
                "icon": p["icon"]
            })
    categories = sorted(df["category"].dropna().unique().tolist()) if not df.empty else []
    return render_template("transactions.html", transactions=txn_list, categories=categories,
                           summary=summary, now=_now(), active_page="transactions")


@main_bp.route("/budgets")
def budgets():
    data_dir = current_app.config["DATA_DIR"]
    df = _load_df(data_dir)
    summary = _get_summary_safe(data_dir)
    budget_list = []
    over_count = 0
    if not df.empty:
        for cat, total in df.groupby("category")["amount"].sum().to_dict().items():
            p = PALETTE.get(cat, DEFAULT_P)
            limit = p["limit"]
            pct = round((total / limit) * 100)
            if pct >= 100:
                sc, sl, bc = "over", "Over budget", "#ff6b6b"
                over_count += 1
            elif pct >= 80:
                sc, sl, bc = "warn", "Near limit", "#f5a623"
            else:
                sc, sl, bc = "ok", "On track", "#00c9a7"
            budget_list.append({
                "category": cat,
                "spent": total,
                "limit": limit,
                "pct": min(pct, 100),
                "status_class": sc,
                "status_label": sl,
                "bar_color": bc,
                "icon": p["icon"],
                "bg": p["bg"]
            })
    return render_template("budgets.html", budgets=budget_list, budget_over_count=over_count,
                           summary=summary, now=_now(), active_page="budgets")


@main_bp.route("/schedule")
def schedule():
    upcoming = [
        {"day": 1,  "month": "Jul", "title": "Rent",             "amount": 15000, "recurring": True},
        {"day": 5,  "month": "Jul", "title": "Internet Bill",     "amount": 999,   "recurring": True},
        {"day": 10, "month": "Jul", "title": "Gym Membership",    "amount": 1500,  "recurring": True},
        {"day": 15, "month": "Jul", "title": "Netflix",           "amount": 649,   "recurring": True},
        {"day": 20, "month": "Jul", "title": "Insurance Premium", "amount": 3200,  "recurring": False},
        {"day": 28, "month": "Jul", "title": "Electricity Bill",  "amount": 1800,  "recurring": True},
    ]
    return render_template("schedule.html", upcoming=upcoming,
                           event_days=[e["day"] for e in upcoming], now=_now(), active_page="schedule")


@main_bp.route("/settings")
def settings():
    return render_template("settings.html", now=_now(), active_page="settings")