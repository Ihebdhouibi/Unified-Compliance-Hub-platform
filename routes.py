from flask import (
    render_template,
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
from datetime import datetime

# Create the blueprint without referencing app directly
auth_bp = Blueprint("auth", __name__)

# Create 2nd blueprint for logged-in pages
dashboard_bp = Blueprint("dashboard", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page route"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid email or password", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page route"""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check for existing username or email
        if User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            flash("Username or email already exists", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page route"""
    return render_template("dashboard.html")
