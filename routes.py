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
from models import (
    Assessment,
    AssessmentResult,
    ComplianceControl,
    ComplianceFramework,
    Organization,
)

# Create the blueprint without referencing app directly
auth_bp = Blueprint("auth", __name__)

# Create 2nd blueprint for logged-in pages
dashboard_bp = Blueprint("dashboard", __name__)

# assessment blueprint
assessment_bp = Blueprint("assessment", __name__)


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


@assessment_bp.route("/assessment", methods=["GET", "POST"])
@login_required
def assessment():
    """Assessment page for policy evaluation"""
    from datetime import datetime

    if request.method == "POST":
        data = request.form

        # Create new assessment
        # Get the first organization for the current user
        user_org = Organization.query.filter_by(user_id=current_user.id).first()

        if not user_org:
            flash("You need to create an organization first", "danger")
            return redirect(url_for("dashboard"))

        new_assessment = Assessment(
            title=data.get("assessment_title", "New Assessment"),
            organization_id=user_org.id,
        )
        db.session.add(new_assessment)
        db.session.flush()  # Get ID without committing

        # Process each control result
        for key, value in data.items():
            if key.startswith("control_"):
                control_id = int(key.split("_")[1])
                status = value
                risk_level = data.get(f"risk_{control_id}", "medium")
                evidence = data.get(f"evidence_{control_id}", "")
                action = data.get(f"action_{control_id}", "")

                result = AssessmentResult(
                    assessment_id=new_assessment.id,
                    control_id=control_id,
                    status=status,
                    risk_level=risk_level,
                    evidence=evidence,
                    action_required=action,
                )
                db.session.add(result)

        db.session.commit()
        flash("Assessment saved successfully", "success")
        return redirect(url_for("dashboard"))

    # GET request handling
    iso_framework = ComplianceFramework.query.filter_by(name="ISO 27001").first()
    pci_framework = ComplianceFramework.query.filter_by(name="PCI DSS").first()
    all_controls = []

    if iso_framework:
        iso_controls = ComplianceControl.query.filter_by(
            framework_id=iso_framework.id
        ).all()
        all_controls.extend(iso_controls)

    if pci_framework:
        pci_controls = ComplianceControl.query.filter_by(
            framework_id=pci_framework.id
        ).all()
        all_controls.extend(pci_controls)

    # Get current date for assessment title default
    now = datetime.now()

    return render_template("assessment.html", controls=all_controls, now=now)
