import os
from flask import Flask
 
 
def create_app():
    app = Flask(__name__)
 
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config["DATA_DIR"] = os.path.join(BASE_DIR, "data")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
 
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
 
    print(f"[PocketBuddy] DATA_DIR = {app.config['DATA_DIR']}")
    csv_path = os.path.join(app.config["DATA_DIR"], "daily_spending.csv")
    print(f"[PocketBuddy] CSV exists: {os.path.exists(csv_path)}")
 
    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        print("[PocketBuddy] .env loaded")
    except ImportError:
        pass
 
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        print("[PocketBuddy] ANTHROPIC_API_KEY found — AI chatbot active")
    else:
        print("[PocketBuddy] No ANTHROPIC_API_KEY — using smart fallback chatbot")
 
    from routes.main_routes import main_bp
    app.register_blueprint(main_bp)
 
    from routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api")
 
    return app
 
 
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)