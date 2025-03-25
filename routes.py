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

# Create the blueprint without referencing app directly
auth_bp = Blueprint("auth", __name__)

# Create 2nd blueprint for logged-in pages
dashboard_bp = Blueprint("dashboard", __name__)


@auth_bp.route("/login", methods=["GET"])
def login():
    """Login page route"""
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET"])
def register():
    """Register page route"""
    return render_template("register.html")


@dashboard_bp.route("/dashboard")
def dashboard():
    """Dashboard page route"""
    return render_template("dashboard.html")
