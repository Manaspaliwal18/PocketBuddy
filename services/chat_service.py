import os
import re
import json
import requests
from services.insight_service import get_summary


def _load_context(data_dir: str) -> str:
    """Build a compact financial context string from CSV data."""
    file_path = os.path.join(data_dir, "daily_spending.csv")
    if not os.path.exists(file_path):
        return "No spending data available yet."

    try:
        summary = get_summary(file_path)
        ctx = (
            f"Financial summary for the current month:\n"
            f"- Total spent: ₹{summary['total_spent']}\n"
            f"- Top spending category: {summary['top_category']}\n"
            f"- Daily average: ₹{summary['avg_daily']}\n"
            f"- Number of transactions: {summary['num_transactions']}\n"
            f"- Category breakdown: {json.dumps(summary['category_breakdown'], indent=2)}\n"
        )
        insight_msgs = [i["message"] for i in summary.get("insights", [])]
        if insight_msgs:
            clean = [re.sub(r"<[^>]+>", "", m) for m in insight_msgs]
            ctx += "- AI Insights:\n" + "\n".join(f"  • {m}" for m in clean)
        return ctx
    except Exception as e:
        return f"Could not load financial data: {e}"


SYSTEM_PROMPT = """You are PocketBuddy AI — a sharp, friendly personal finance advisor \
embedded in the PocketBuddy dashboard. You have access to the user's real spending data \
for the current month (provided below).

Your role:
• Answer questions about their spending, categories, and trends
• Give concrete, actionable saving tips
• Flag budget risks clearly but kindly
• Keep replies concise — 2-4 sentences unless a detailed breakdown is needed
• Use ₹ (Indian Rupee) for all monetary values
• Never make up data not present in the context
• Format responses with bullet points when listing items

Financial context:
{context}
"""


def chat(messages: list, data_dir: str) -> str:
    """
    Send a conversation to Google Gemini API via HTTP and return the assistant reply.
    Falls back to rule-based responses if no API key is set.
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return _fallback_chat(messages, data_dir)

    context = _load_context(data_dir)
    system_prompt = SYSTEM_PROMPT.format(context=context)

    # Build conversation text
    conversation_text = system_prompt + "\n\n"
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            conversation_text += f"User: {content}\n"
        else:
            conversation_text += f"Assistant: {content}\n"

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}",
            headers={
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": conversation_text}
                        ]
                    }
                ]
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception:
        return _fallback_chat(messages, data_dir)


def _fallback_chat(messages: list, data_dir: str) -> str:
    """Rule-based smart fallback when API is unavailable."""
    if not messages:
        return "Please ask something about your finances."

    user_query = messages[-1]["content"].lower()

    file_path = os.path.join(data_dir, "daily_spending.csv")
    if not os.path.exists(file_path):
        return "No financial data available yet. Please add some spending records first."

    try:
        summary = get_summary(file_path)
    except Exception:
        return "Unable to load financial data at the moment."

    total = summary.get("total_spent", "0")
    top_category = summary.get("top_category", "N/A")
    breakdown = summary.get("category_breakdown", {})
    avg = summary.get("avg_daily", "0")
    num_txn = summary.get("num_transactions", 0)

    if any(w in user_query for w in ["top", "highest", "most", "category"]):
        amt = breakdown.get(top_category, 0)
        return f"Your highest spending category is {top_category} at ₹{amt:,.0f} this month. Consider setting a stricter budget for this category."

    elif any(w in user_query for w in ["total", "spend", "spent", "much"]):
        return f"Your total spending this month is ₹{total}. You've made {num_txn} transactions with a daily average of ₹{avg}."

    elif any(w in user_query for w in ["average", "daily", "avg"]):
        return f"Your daily average spending is ₹{avg}. Keeping this under ₹1,500/day would help you save significantly."

    elif any(w in user_query for w in ["save", "reduce", "cut", "less", "tip"]):
        return (
            f"Here are some tips to save more:\n"
            f"• Reduce spending in {top_category} — your top expense\n"
            f"• Set a daily spending limit of ₹1,500\n"
            f"• Track every transaction to spot patterns\n"
            f"• Review your ₹{avg}/day average weekly"
        )

    elif any(w in user_query for w in ["breakdown", "categories", "all"]):
        lines = ["Here is your category-wise spending this month:\n"]
        for cat, amt in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"• {cat}: ₹{amt:,.0f}")
        return "\n".join(lines)

    elif any(w in user_query for w in ["over", "exceed", "limit", "budget"]):
        LIMITS = {"Food & Dining": 7000, "Transport": 5000, "Shopping": 6000,
                  "Utilities": 4000, "Entertainment": 3000, "Health": 3000, "Food": 7000}
        over = [(c, a, LIMITS.get(c, 5000)) for c, a in breakdown.items() if a > LIMITS.get(c, 5000)]
        if over:
            lines = ["You are over budget in:\n"]
            for cat, spent, limit in over:
                lines.append(f"• {cat}: ₹{spent:,.0f} / ₹{limit:,} limit")
            return "\n".join(lines)
        else:
            return "Great news! You are within budget in all categories this month. Keep it up!"

    else:
        return (
            f"Based on your data this month:\n"
            f"• Total spent: ₹{total}\n"
            f"• Top category: {top_category}\n"
            f"• Daily average: ₹{avg}\n"
            f"• Transactions: {num_txn}\n\n"
            f"Ask me about breakdown, saving tips, or budget status!"
        )