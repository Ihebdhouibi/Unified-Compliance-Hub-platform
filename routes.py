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
    ControlMapping,
)
import logging

# Create the blueprint without referencing app directly
auth_bp = Blueprint("auth", __name__)

# Create 2nd blueprint for logged-in pages
dashboard_bp = Blueprint("dashboard", __name__)

# assessment blueprint
assessment_bp = Blueprint("assessment", __name__)

# api assessment blueprint
api_assessment_bp = Blueprint("api/assessment", __name__)

# controls blueprint
controls_bp = Blueprint("controls", __name__)

# reports blueprint
reports_bp = Blueprint("reports", __name__)


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
    """User registration route"""
    if request.method == "POST":
        try:
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            logging.debug(
                f"Registration attempt for username: {username}, email: {email}"
            )

            # Check if username or email already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                flash("Username or email already exists", "danger")
                return redirect(url_for("auth.register"))

            # Create new user
            try:
                new_user = User(username=username, email=email)
                logging.debug("User object created")

                try:
                    new_user.set_password(password)
                    logging.debug("Password set successfully")

                    db.session.add(new_user)
                    logging.debug("User added to session")

                    db.session.flush()  # This gets the ID without committing
                    logging.debug(f"User ID generated: {new_user.id}")
                except ValueError as e:
                    logging.error(f"Password validation error: {str(e)}")
                    flash(str(e), "danger")
                    return redirect(url_for("auth.register"))
                except Exception as e:
                    logging.error(f"Error during user creation: {str(e)}")
                    flash("Error creating user account", "danger")
                    return redirect(url_for("auth.register"))

                # Create default organization for the user
                try:
                    new_org = Organization(
                        name=f"{username}'s Organization", owner_id=new_user.id
                    )
                    logging.debug("Organization object created")

                    db.session.add(new_org)
                    logging.debug("Organization added to session")

                    db.session.commit()
                    logging.debug("Database transaction committed")

                    flash("Registration successful! Please log in.", "success")
                    return redirect(url_for("auth.login"))
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error creating organization: {str(e)}")
                    flash("Error creating organization", "danger")
                    return redirect(url_for("auth.register"))
            except Exception as e:
                logging.error(f"Error in user registration: {str(e)}")
                flash("Registration error", "danger")
                return redirect(url_for("auth.register"))
        except Exception as e:
            logging.error(f"Unexpected error in registration route: {str(e)}")
            flash("An unexpected error occurred", "danger")
            return redirect(url_for("auth.register"))

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
    """Dashboard route displaying compliance overview"""
    # Get most recent assessment if available
    assessment = Assessment.query.order_by(Assessment.date_created.desc()).first()
    if assessment:
        assessment_id = assessment.id
    else:
        assessment_id = None

    return render_template("dashboard.html", assessment_id=assessment_id)


@assessment_bp.route("/assessment", methods=["GET", "POST"])
@login_required
def assessment():
    """Assessment page for policy evaluation"""
    from datetime import datetime

    if request.method == "POST":
        data = request.form

        # Create new assessment
        # Get the first organization for the current user
        user_org = Organization.query.filter_by(owner_id=current_user.id).first()

        if not user_org:
            flash("You need to create an organization first", "danger")
            return redirect(url_for("dashboard.dashboard"))

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
        return redirect(url_for("dashboard.dashboard"))

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


@controls_bp.route("/controls")
def controls():
    """View unified control framework"""
    # Get ISO controls
    iso_framework = ComplianceFramework.query.filter_by(name="ISO 27001").first()
    iso_controls = (
        ComplianceControl.query.filter_by(framework_id=iso_framework.id).all()
        if iso_framework
        else []
    )

    # Get PCI DSS controls
    pci_framework = ComplianceFramework.query.filter_by(name="PCI DSS").first()
    pci_controls = (
        ComplianceControl.query.filter_by(framework_id=pci_framework.id).all()
        if pci_framework
        else []
    )

    # Get mappings
    mappings = ControlMapping.query.all()
    mapping_dict = {}

    for mapping in mappings:
        primary = mapping.primary_control
        secondary = mapping.secondary_control
        if primary.id not in mapping_dict:
            mapping_dict[primary.id] = []
        mapping_dict[primary.id].append(
            {
                "id": secondary.id,
                "control_id": secondary.control_id,
                "title": secondary.title,
                "relationship": mapping.relationship_type,
            }
        )

    return render_template(
        "controls.html",
        iso_controls=iso_controls,
        pci_controls=pci_controls,
        mappings=mapping_dict,
    )


@reports_bp.route("/reports")
def reports():
    """Reports page for detailed compliance reports"""
    assessments = Assessment.query.order_by(Assessment.date_created.desc()).all()
    return render_template("reports.html", assessments=assessments)


@api_assessment_bp.route("/api/assessment/<int:assessment_id>")
def get_assessment_data(assessment_id):
    """API endpoint to get assessment data for charts"""
    results = AssessmentResult.query.filter_by(assessment_id=assessment_id).all()
    print(results)
    # Count by status
    status_counts = {"compliant": 0, "partially_compliant": 0, "non_compliant": 0}

    # Count by risk level
    risk_counts = {"high": 0, "medium": 0, "low": 0}

    # Get framework compliance percentages
    iso_compliance = {"total": 0, "compliant": 0}
    pci_compliance = {"total": 0, "compliant": 0}

    for result in results:
        # Update status counts
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

        # Update risk counts
        risk_counts[result.risk_level] = risk_counts.get(result.risk_level, 0) + 1

        # Update framework-specific counts
        control = result.control
        framework = control.framework

        if framework.name == "ISO 27001":
            iso_compliance["total"] += 1
            if result.status == "compliant":
                iso_compliance["compliant"] += 1
        elif framework.name == "PCI DSS":
            pci_compliance["total"] += 1
            if result.status == "compliant":
                pci_compliance["compliant"] += 1

    # Calculate percentages
    iso_percentage = (
        (iso_compliance["compliant"] / iso_compliance["total"] * 100)
        if iso_compliance["total"] > 0
        else 0
    )
    pci_percentage = (
        (pci_compliance["compliant"] / pci_compliance["total"] * 100)
        if pci_compliance["total"] > 0
        else 0
    )

    # Prepare detailed results
    detailed_results = []
    for result in results:
        control = result.control
        detailed_results.append(
            {
                "id": control.id,
                "control_id": control.control_id,
                "title": control.title,
                "framework": control.framework.name,
                "status": result.status,
                "risk_level": result.risk_level,
                "action_required": result.action_required,
            }
        )

    data = {
        "status_counts": status_counts,
        "risk_counts": risk_counts,
        "framework_compliance": {"iso27001": iso_percentage, "pcidss": pci_percentage},
        "overall_compliance": (
            (
                (iso_compliance["compliant"] + pci_compliance["compliant"])
                / (iso_compliance["total"] + pci_compliance["total"])
                * 100
            )
            if (iso_compliance["total"] + pci_compliance["total"]) > 0
            else 0
        ),
        "detailed_results": detailed_results,
    }

    return jsonify(data)
