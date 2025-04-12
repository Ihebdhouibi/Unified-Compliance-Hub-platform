import torch
from transformers import BertTokenizer, BertForSequenceClassification

# Load the trained model and tokenizer
model_dir = "saved_model"
tokenizer = BertTokenizer.from_pretrained(model_dir)
model = BertForSequenceClassification.from_pretrained(model_dir)
model.eval()

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Test samples
samples = [
    (
        "A.9.4",
        "System and application access control",
        "Sharedadmincredentials usedroutinely",
    ),
    (
        "4.1",
        "Use strong cryptography and security protocols",
        "SSLv3stillallowed forcompatibility with TLS1.3enforced network-wide",
    ),
    (
        "1.1",
        "Establish and implement firewall and router configuration standards",
        "No current security measures taken",
    ),
    (
        "A.12.1",
        "Operational procedures and responsibilities",
        "The organization does not have a policy for monitoring and controlling system access to sensitive data.",
    ),
    (
        "A.8.1",
        "Asset management",
        "The organization does not regularly monitor physical security measures, leading to potential breaches.",
    ),
    (
        "A.8.1",
        "Asset management",
        "Sensitive assets are clearly identified",
    ),
    (
        "A.5.1",
        "Information security policies",
        "The policy is designed to meet industry standards and comply with applicable regulations, such as GDPR, HIPAA, and PCI DSS.",
    ),
    (
        "A.5.1",
        "Information security policies",
        "Our information security policy is reviewed and approved quarterly by CISO and the Board. All departments acknowledge the policy via the HR portal. It’s version-controlled and distributed across all business units",
    ),
    (
        "A.5.1",
        "OInformation security policies",
        "Policy documents are stored centrally, yet not communicated to all employees.",
    ),
]

# Label map
label_map = {0: "Fully Compliant", 1: "Non-Compliant", 2: "Partially-Compliant"}

# Predict and display results
print("\n=== Model Predictions ===")
for control_id, title, measure in samples:
    input_text = control_id + " " + title + " " + measure
    encoded = tokenizer(
        input_text,
        truncation=True,
        padding="max_length",
        max_length=256,
        return_tensors="pt",
    )

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        prediction = torch.argmax(outputs.logits, dim=1).item()
        label = label_map[prediction]

    print(
        f"\nControl: {control_id} | Title: {title}\nMeasure: {measure}\nPrediction: {label}"
    )
