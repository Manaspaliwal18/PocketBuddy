import os
from flask import Flask
 
def create_app():
    app = Flask(__name__)
 
    # Absolute path to data/ folder — always resolves correctly
    # regardless of which directory you run `python app.py` from
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config["DATA_DIR"] = os.path.join(BASE_DIR, "data")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
 
    # Create data dir if missing
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
 
    # Log the resolved path so you can verify in terminal
    print(f"[PocketBuddy] DATA_DIR = {app.config['DATA_DIR']}")
    csv = os.path.join(app.config["DATA_DIR"], "daily_spending.csv")
    print(f"[PocketBuddy] CSV exists: {os.path.exists(csv)}")
 
    # Load .env file if present (optional, needs python-dotenv)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        print("[PocketBuddy] .env loaded")
    except ImportError:
        pass
 
    # Register blueprints
    from routes.main_routes import main_bp
    app.register_blueprint(main_bp)
 
    from routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api")
 
    return app
 
 
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)