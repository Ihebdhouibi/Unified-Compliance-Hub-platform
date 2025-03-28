"""
Initial data loader for compliance frameworks, controls, and mappings
"""

import logging
from sqlalchemy import exc


def load_initial_data(db):
    """
    Load initial compliance framework data if not already present
    """
    from models import ComplianceFramework, ComplianceControl, ControlMapping

    # Check if data already exists
    frameworks = ComplianceFramework.query.all()
    if frameworks:
        logging.info("Compliance frameworks already exist, skipping initialization")
        return

    logging.info("Initializing compliance frameworks and controls")

    # Create ISO 27001 framework
    iso_framework = ComplianceFramework(name="ISO 27001", version="2022")
    db.session.add(iso_framework)
    db.session.flush()  # Get ID without committing

    # Create PCI DSS framework
    pci_framework = ComplianceFramework(name="PCI DSS", version="4.0")
    db.session.add(pci_framework)
    db.session.flush()  # Get ID without committing

    # Define ISO 27001 controls (sample subset)
    iso_controls = [
        {
            "control_id": "A.5.1",
            "title": "Information security policies",
            "description": "To provide management direction and support for information security in accordance with business requirements and relevant laws and regulations.",
        },
        {
            "control_id": "A.5.2",
            "title": "Information security roles and responsibilities",
            "description": "To establish a framework of roles and responsibilities for information security implementation.",
        },
        {
            "control_id": "A.6.1",
            "title": "Access control policy",
            "description": "To limit access to information and information processing facilities.",
        },
        {
            "control_id": "A.6.2",
            "title": "User access management",
            "description": "To ensure authorized user access and to prevent unauthorized access to systems and services.",
        },
        {
            "control_id": "A.8.1",
            "title": "Asset management",
            "description": "Responsibility for assets: To identify organizational assets and define appropriate protection responsibilities.",
        },
        {
            "control_id": "A.8.2",
            "title": "Information classification",
            "description": "To ensure that information receives an appropriate level of protection in accordance with its importance to the organization.",
        },
        {
            "control_id": "A.9.1",
            "title": "Business requirements of access control",
            "description": "To limit access to information and information processing facilities.",
        },
        {
            "control_id": "A.9.4",
            "title": "System and application access control",
            "description": "To prevent unauthorized access to systems and applications.",
        },
        {
            "control_id": "A.12.1",
            "title": "Operational procedures and responsibilities",
            "description": "To ensure correct and secure operations of information processing facilities.",
        },
        {
            "control_id": "A.12.2",
            "title": "Protection from malware",
            "description": "To ensure that information and information processing facilities are protected against malware.",
        },
    ]

    # Define PCI DSS controls (sample subset)
    pci_controls = [
        {
            "control_id": "1.1",
            "title": "Establish and implement firewall and router configuration standards",
            "description": "Establish, implement, and maintain firewall and router configuration standards that include formal processes for approving and testing all network connections and changes to firewall and router configurations.",
        },
        {
            "control_id": "1.2",
            "title": "Build firewall and router configurations that restrict connections",
            "description": "Build firewall and router configurations that restrict connections between untrusted networks and any system components in the cardholder data environment.",
        },
        {
            "control_id": "2.1",
            "title": "Always change vendor defaults",
            "description": "Always change vendor-supplied defaults and remove or disable unnecessary default accounts before installing a system on the network.",
        },
        {
            "control_id": "3.1",
            "title": "Keep cardholder data storage to a minimum",
            "description": "Keep cardholder data storage to a minimum by implementing data retention and disposal policies, procedures and processes.",
        },
        {
            "control_id": "4.1",
            "title": "Use strong cryptography and security protocols",
            "description": "Use strong cryptography and security protocols to safeguard sensitive cardholder data during transmission over open, public networks.",
        },
        {
            "control_id": "5.1",
            "title": "Deploy anti-virus software",
            "description": "Deploy anti-virus software on all systems commonly affected by malicious software.",
        },
        {
            "control_id": "6.1",
            "title": "Establish a process to identify security vulnerabilities",
            "description": "Establish a process to identify security vulnerabilities, using reputable outside sources for security vulnerability information, and assign a risk ranking to newly discovered security vulnerabilities.",
        },
        {
            "control_id": "7.1",
            "title": "Limit access to system components",
            "description": "Limit access to system components and cardholder data to only those individuals whose job requires such access.",
        },
        {
            "control_id": "8.1",
            "title": "Define and implement policies and procedures",
            "description": "Define and implement policies and procedures to ensure proper user identification management for non-consumer users and administrators on all system components.",
        },
        {
            "control_id": "9.1",
            "title": "Use appropriate facility entry controls",
            "description": "Use appropriate facility entry controls to limit and monitor physical access to systems in the cardholder data environment.",
        },
    ]

    # Add ISO controls
    iso_control_objs = {}
    for control_data in iso_controls:
        control = ComplianceControl(
            control_id=control_data["control_id"],
            title=control_data["title"],
            description=control_data["description"],
            framework_id=iso_framework.id,
        )
        db.session.add(control)
        iso_control_objs[control_data["control_id"]] = control

    # Add PCI controls
    pci_control_objs = {}
    for control_data in pci_controls:
        control = ComplianceControl(
            control_id=control_data["control_id"],
            title=control_data["title"],
            description=control_data["description"],
            framework_id=pci_framework.id,
        )
        db.session.add(control)
        pci_control_objs[control_data["control_id"]] = control

    # Commit controls before creating mappings
    db.session.flush()

    # Define control mappings
    mappings = [
        # ISO to PCI
        {"primary": "A.5.1", "secondary": "12.1", "relationship": "equivalent"},
        {"primary": "A.6.1", "secondary": "7.1", "relationship": "equivalent"},
        {"primary": "A.6.2", "secondary": "8.1", "relationship": "partial"},
        {"primary": "A.9.1", "secondary": "7.1", "relationship": "equivalent"},
        {"primary": "A.9.4", "secondary": "8.1", "relationship": "partial"},
        {"primary": "A.12.2", "secondary": "5.1", "relationship": "equivalent"},
        # PCI to ISO
        {"primary": "1.1", "secondary": "A.9.1", "relationship": "partial"},
        {"primary": "2.1", "secondary": "A.9.4", "relationship": "partial"},
        {"primary": "5.1", "secondary": "A.12.2", "relationship": "equivalent"},
        {"primary": "7.1", "secondary": "A.6.1", "relationship": "equivalent"},
        {"primary": "8.1", "secondary": "A.6.2", "relationship": "partial"},
    ]

    # Create control mappings - NOTE: Some secondary controls might not be in our sample data,
    # so we'll handle potential errors
    for mapping_data in mappings:
        primary_id = mapping_data["primary"]
        secondary_id = mapping_data["secondary"]

        # Handle potential missing controls in our sample data
        primary_control = None
        secondary_control = None

        if primary_id.startswith("A."):
            primary_control = iso_control_objs.get(primary_id)
        else:
            primary_control = pci_control_objs.get(primary_id)

        if secondary_id.startswith("A."):
            secondary_control = iso_control_objs.get(secondary_id)
        else:
            secondary_control = pci_control_objs.get(secondary_id)

        # Only create mapping if both controls exist
        if primary_control and secondary_control:
            mapping = ControlMapping(
                primary_control_id=primary_control.id,
                secondary_control_id=secondary_control.id,
                relationship_type=mapping_data["relationship"],
            )
            db.session.add(mapping)

    # Commit all changes
    try:
        db.session.commit()
        logging.info("Initial compliance data loaded successfully")
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error loading initial data: {str(e)}")
        raise
