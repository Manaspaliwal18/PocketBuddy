import os
import pandas as pd

# Resolve paths relative to project root (one level up from services/)
_BASE = os.path.join(os.path.dirname(__file__), "..", "data")

FIXED_EXPENSES_FILE = os.path.join(_BASE, "fixed_expenses.csv")
DAILY_SPENDING_FILE = os.path.join(_BASE, "daily_spending.csv")
CATEGORIES_FILE     = os.path.join(_BASE, "categories.csv")

DEFAULT_CATEGORIES = ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Health", "Food & Dining"]


def _ensure_dir():
    os.makedirs(_BASE, exist_ok=True)


# ── Fixed Expenses ─────────────────────────────────────────────────────────────

def save_fixed_expenses(record: dict) -> None:
    """Appends a new fixed expense to the CSV file."""
    _ensure_dir()
    df, _ = load_fixed_expenses()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(FIXED_EXPENSES_FILE, index=False)


def load_fixed_expenses() -> tuple:
    """Loads all fixed expenses. Returns (DataFrame, total_amount)."""
    try:
        df = pd.read_csv(FIXED_EXPENSES_FILE)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        return df, float(df["amount"].sum())
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["category", "amount"]), 0.0


# ── Daily Spending ─────────────────────────────────────────────────────────────

def save_daily_record(record: dict) -> None:
    """Appends a new daily spending record."""
    _ensure_dir()
    df = load_daily_spending()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(DAILY_SPENDING_FILE, index=False)


def load_daily_spending() -> pd.DataFrame:
    """Loads all daily spending records."""
    try:
        return pd.read_csv(DAILY_SPENDING_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["date", "amount", "category"])


# ── Categories ─────────────────────────────────────────────────────────────────

def load_categories() -> list:
    """Loads expense categories, falling back to defaults."""
    try:
        df = pd.read_csv(CATEGORIES_FILE)
        return df["category"].dropna().tolist()
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return DEFAULT_CATEGORIES


def save_categories(categories_list: list) -> None:
    """Saves the current list of categories."""
    _ensure_dir()
    pd.DataFrame(categories_list, columns=["category"]).to_csv(CATEGORIES_FILE, index=False)