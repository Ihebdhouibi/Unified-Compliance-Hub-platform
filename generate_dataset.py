import json
import pandas as pd
import random
from faker import Faker

fake = Faker()


# Load data files
def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)


controls = load_json("controls.txt")
scenarios = load_json("controls.json")

# Compliance assignment logic
COMPLIANCE_RULES = {
    "Fully Compliant": [
        "automated",
        "real-time",
        "enforced",
        "MFA",
        "biometric",
        "tokenization",
        "immutable",
        "integrated",
        "Zero Trust",
        "JIT",
    ],
    "Partially Compliant": [
        "manual",
        "quarterly",
        "basic",
        "periodic",
        "documented",
        "scheduled",
        "reviewed",
        "biannual",
        "partial",
        "legacy",
    ],
    "Non-Compliant": [
        "missing",
        "outdated",
        "expired",
        "disabled",
        "unencrypted",
        "shared credentials",
        "no formal",
        "not enforced",
        "excluded",
        "bypassed",
        "exception",
    ],
}


def assign_compliance(scenario):
    scenario_lower = scenario.lower()
    for status, keywords in COMPLIANCE_RULES.items():
        if any(kw in scenario_lower for kw in keywords):
            return status
    return random.choices(
        list(COMPLIANCE_RULES.keys()), weights=[0.33, 0.33, 0.33], k=1
    )[0]


# Generate dataset
NUM_ORGANIZATIONS = 350
CONTROL_IDS = [c["control_id"] for c in controls]

dataset = []
for org_id in range(1, NUM_ORGANIZATIONS + 1):
    org_entries = []

    for control in controls:
        control_id = control["control_id"]
        scenario = random.choice(scenarios[control_id])

        entry = {
            "organization_id": f"ORG-{org_id:03d}",
            "control_id": control_id,
            "title": control["title"],
            "description": control["description"],
            "Framework": "PCI DSS" if "." in control_id else "ISO 27001",
            "Current Measures": scenario,
            "Compliance Status": assign_compliance(scenario),
            "Implementation Details": "",
            "Recommendations": "",
        }

        # Set derived fields
        status = entry["Compliance Status"]
        if status == "Fully Compliant":
            entry["Implementation Details"] = (
                "Complete implementation meeting all requirements"
            )
            entry["Recommendations"] = "Maintain current controls"
        elif status == "Partially Compliant":
            entry["Implementation Details"] = (
                f'Partial implementation: {fake.random_element(["gaps exist", "manual processes", "limited coverage"])}'
            )
            entry["Recommendations"] = "Enhance automation and monitoring"
        else:
            entry["Implementation Details"] = "Critical security gaps identified"
            entry["Recommendations"] = "Immediate remediation required"

        org_entries.append(entry)

    random.shuffle(org_entries)
    dataset.extend(org_entries)

# Create and validate DataFrame
df = pd.DataFrame(dataset)

# Validation checks
assert len(df) == NUM_ORGANIZATIONS * len(
    CONTROL_IDS
), "Missing controls in some organizations"
assert df["control_id"].nunique() == len(CONTROL_IDS), "Missing control IDs"

# Save dataset
df.to_csv("compliance_dataset_v4.csv", index=False)

print(f"Generated {len(df)} records")
print("Compliance distribution:")
print(df["Compliance Status"].value_counts(normalize=True))
