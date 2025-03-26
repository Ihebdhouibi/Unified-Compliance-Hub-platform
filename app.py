from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()
load_dotenv(dotenv_path=".env")


def create_app():
    app = Flask(__name__, static_folder="static")

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    print("SECRET_KEY:", os.getenv("SECRET_KEY"))
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import routes after creating the app to avoid circular imports
    from routes import auth_bp, dashboard_bp
    from models import User

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # Configure login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
