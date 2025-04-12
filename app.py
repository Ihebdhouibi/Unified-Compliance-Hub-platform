from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, logout_user, current_user
from flask_cors import CORS
from datetime import timedelta
from dotenv import load_dotenv
import os
import logging
import time

db = SQLAlchemy()
login_manager = LoginManager()
load_dotenv(dotenv_path=".env")


def create_app():
    app = Flask(__name__, static_folder="static")
    CORS(app)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    # close session in case of inactivity
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False

    print("SECRET_KEY:", os.getenv("SECRET_KEY"))
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Session expired. Please log in again."
    login_manager.login_message_category = "warning"

    with app.app_context():
        from data.compliance_mapping import load_initial_data

        try:
            load_initial_data(db)
            logging.info("Initial data loaded successfully or already exists")
        except Exception as e:
            logging.error(f"Error initializing data: {str(e)}")
    # with app.app_context():
    #    db.create_all()
    # Import routes after creating the app to avoid circular imports
    from routes import (
        auth_bp,
        dashboard_bp,
        assessment_bp,
        controls_bp,
        reports_bp,
        api_assessment_bp,
        report_gen_bp,
        extract_policies_bp,
        prediction_bp,
    )
    from models import User

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(assessment_bp, url_prefix="/assessment")
    app.register_blueprint(controls_bp, url_prefix="/controls")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(api_assessment_bp, url_prefix="/api/assessment")
    app.register_blueprint(report_gen_bp, url_prefix="/generate-milestone-report")
    app.register_blueprint(extract_policies_bp, url_prefix="/extract-text")
    app.register_blueprint(prediction_bp, url_prefix="/predict")

    # Configure login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.before_request
    def check_session_timeout():
        if current_user.is_authenticated:
            now = time.time()
            last_activity = session.get("last_activity", now)
            session["last_activity"] = now

            timeout_seconds = app.config["PERMANENT_SESSION_LIFETIME"].total_seconds()

            if now - last_activity > timeout_seconds:
                logout_user()
                session.clear()
                return redirect(url_for("auth_bp.login"))

    return app
