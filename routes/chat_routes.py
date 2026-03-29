from flask import Blueprint, request, jsonify, current_app
from services.chat_service import chat
 
chat_bp = Blueprint("chat", __name__)
 
 
@chat_bp.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    Expects JSON body:
    {
        "messages": [
            {"role": "user", "content": "..."},
            ...
        ]
    }
    Returns:
    {
        "reply": "..."
    }
    """
    body = request.get_json(silent=True)
    if not body or "messages" not in body:
        return jsonify({"error": "Missing 'messages' in request body."}), 400
 
    messages = body["messages"]
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "'messages' must be a non-empty list."}), 400
 
    # Validate each message
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            return jsonify({"error": "Each message must have 'role' and 'content'."}), 400
        if msg["role"] not in ("user", "assistant"):
            return jsonify({"error": "Message role must be 'user' or 'assistant'."}), 400
 
    try:
        data_dir = current_app.config["DATA_DIR"]
        reply = chat(messages, data_dir)
        return jsonify({"reply": reply})
    except Exception as e:
        current_app.logger.error("Chat error: %s", e)
        return jsonify({"error": "AI service unavailable. Please try again."}), 503