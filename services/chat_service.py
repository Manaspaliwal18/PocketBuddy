import os
import json
import anthropic
import pandas as pd
from services.insight_service import get_summary
 
_client = None
 
def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return _client
 
 
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
            # Strip HTML tags for plain-text context
            import re
            clean = [re.sub(r"<[^>]+>", "", m) for m in insight_msgs]
            ctx += "- AI Insights:\n" + "\n".join(f"  • {m}" for m in clean)
        return ctx
    except Exception as e:
        return f"Could not load financial data: {e}"
 
 
SYSTEM_PROMPT = """You are PocketBuddy AI — a sharp, friendly personal finance advisor 
embedded in the PocketBuddy dashboard. You have access to the user's real spending data 
for the current month (provided below). 
 
Your role:
• Answer questions about their spending, categories, and trends
• Give concrete, actionable saving tips
• Flag budget risks clearly but kindly
• Keep replies concise — 2-4 sentences unless a detailed breakdown is needed
• Use ₹ (Indian Rupee) for all monetary values
• Never make up data not present in the context
 
Financial context:
{context}
"""
 
 
def chat(messages: list[dict], data_dir: str) -> str:
    """
    Send a conversation to Claude and return the assistant reply.
 
    `messages` is a list of {"role": "user"|"assistant", "content": str} dicts.
    """
    context = _load_context(data_dir)
    system = SYSTEM_PROMPT.format(context=context)
 
    client = _get_client()
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=system,
        messages=messages,
    )
    return response.content[0].text