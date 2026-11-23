"""
CodePulse AI - Main Application Entry Point.
"""
from flask import Flask, render_template
from flask_cors import CORS
from api.routes import api_bp
from config import Config

def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static"
    )
    app.config.from_object(Config)
    
    # Enable CORS for REST clients
    CORS(app)

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    print("\n" + "="*50)
    print(f">> CODEPULSE AI - Server Starting on http://localhost:{Config.PORT}")
    print(">> Multi-Language AI Code Quality & Security Analyzer")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=Config.PORT, debug=False, use_reloader=False)
