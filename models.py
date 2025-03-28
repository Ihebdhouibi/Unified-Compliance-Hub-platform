from flask_login import UserMixin
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum, Index

# Enum definitions for better data integrity
COMPLIANCE_STATUS = Enum(
    "compliant", "partially_compliant", "non_compliant", name="compliance_status"
)

RISK_LEVEL = Enum("high", "medium", "low", name="risk_level")

RELATIONSHIP_TYPE = Enum("equivalent", "partial", "superset", name="relationship_type")

DOCUMENT_STATUS = Enum("pending", "analyzed", "compliant", name="document_status")


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default="user", nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    organizations = db.relationship("Organization", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    assessments = db.relationship(
        "Assessment", backref="organization", lazy=True, cascade="all, delete-orphan"
    )
    documents = db.relationship(
        "ComplianceDocument",
        backref="organization",
        lazy=True,
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_organizations_name", "name"),)


class ComplianceFramework(db.Model):
    __tablename__ = "compliance_frameworks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(20), nullable=False)

    controls = db.relationship(
        "ComplianceControl",
        backref="framework",
        lazy=True,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint("name", "version", name="uix_framework_name_version"),
        Index("ix_frameworks_name", "name"),
    )


class ComplianceControl(db.Model):
    __tablename__ = "compliance_controls"

    id = db.Column(db.Integer, primary_key=True)
    control_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    framework_id = db.Column(
        db.Integer, db.ForeignKey("compliance_frameworks.id"), nullable=False
    )

    # Relationships for control mappings
    primary_mappings = db.relationship(
        "ControlMapping",
        foreign_keys="ControlMapping.primary_control_id",
        backref="primary_control",
        cascade="all, delete-orphan",
    )
    secondary_mappings = db.relationship(
        "ControlMapping",
        foreign_keys="ControlMapping.secondary_control_id",
        backref="secondary_control",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "control_id", "framework_id", name="uix_control_id_framework"
        ),
        Index("ix_controls_control_id", "control_id"),
    )


class ControlMapping(db.Model):
    __tablename__ = "control_mappings"

    id = db.Column(db.Integer, primary_key=True)
    primary_control_id = db.Column(
        db.Integer, db.ForeignKey("compliance_controls.id"), nullable=False
    )
    secondary_control_id = db.Column(
        db.Integer, db.ForeignKey("compliance_controls.id"), nullable=False
    )
    relationship_type = db.Column(RELATIONSHIP_TYPE, nullable=False)
    description = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint(
            "primary_control_id", "secondary_control_id", name="uix_control_mapping"
        ),
    )


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )

    results = db.relationship(
        "AssessmentResult",
        backref="assessment",
        lazy=True,
        cascade="all, delete-orphan",
    )


class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False
    )
    control_id = db.Column(
        db.Integer, db.ForeignKey("compliance_controls.id"), nullable=False
    )
    status = db.Column(COMPLIANCE_STATUS, nullable=False)
    evidence = db.Column(db.Text)
    risk_level = db.Column(RISK_LEVEL, nullable=False)
    action_required = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    control = db.relationship("ComplianceControl")

    __table_args__ = (
        Index("ix_results_assessment_control", "assessment_id", "control_id"),
    )


class ComplianceDocument(db.Model):
    __tablename__ = "compliance_documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    document_type = db.Column(db.String(50), nullable=False)
    status = db.Column(DOCUMENT_STATUS, default="pending", nullable=False)
    analysis_results = db.Column(db.Text)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    uploader = db.relationship("User", backref="uploads")

    __table_args__ = (
        Index("ix_documents_status", "status"),
        Index("ix_documents_type", "document_type"),
    )
