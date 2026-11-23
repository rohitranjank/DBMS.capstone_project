import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/campus_complaints"),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false") == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=64 * 1024)
    if test_config: app.config.update(test_config)
    CORS(app, origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")], supports_credentials=True)
    db.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)
    # Serve the built React app from Flask so one deployment (one URL) works for everyone.
    dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static_dist")
    if os.path.isdir(dist):
        from flask import abort, send_from_directory
        @app.get("/", defaults={"p": ""})
        @app.get("/<path:p>")
        def spa(p):
            if p.startswith("api/"): abort(404)
            return send_from_directory(dist, p if p and os.path.isfile(os.path.join(dist, p)) else "index.html")
    return app
