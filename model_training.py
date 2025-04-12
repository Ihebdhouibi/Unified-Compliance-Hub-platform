import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import BertTokenizer, BertForSequenceClassification, AutoConfig
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
import os
from datetime import datetime
from tqdm import tqdm

# Hyperparameters
BATCH_SIZE = 16
EPOCHS = 20  # Can go up to 20 with early stopping
PATIENCE = 3  # Early stopping patience
MAX_LEN = 256
MODEL_NAME = "bert-base-uncased"

# Log setup
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f"training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)


def log(message):
    print(message)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


# Dataset class
class ComplianceDataset(Dataset):
    def __init__(self, df, tokenizer, max_len):
        self.tokenizer = tokenizer
        self.texts = df["text"].to_numpy()
        self.labels = df["label"].to_numpy()
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        )
        return {
            "text": text,
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
        }


# Load data
train_df = pd.read_csv("data/train.csv")
val_df = pd.read_csv("data/val.csv")
test_df = pd.read_csv("data/test.csv")

# Class weights
class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(train_df["label"]),
    y=train_df["label"].values,
)
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float)

# Tokenizer
tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)

# Datasets and loaders
train_ds = ComplianceDataset(train_df, tokenizer, MAX_LEN)
val_ds = ComplianceDataset(val_df, tokenizer, MAX_LEN)
test_ds = ComplianceDataset(test_df, tokenizer, MAX_LEN)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE)

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
log(f"Using device: {device}")
class_weights_tensor = class_weights_tensor.to(device)

# Load model
try:
    config = AutoConfig.from_pretrained(MODEL_NAME, num_labels=3)
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, config=config)
except Exception:
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

model.to(device)
optimizer = AdamW(model.parameters(), lr=0.0001)

# Training loop with early stopping
log("🚀 Starting training...")
best_val_f1 = 0
patience_counter = 0

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        loss_fn = torch.nn.CrossEntropyLoss()
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(train_loader)
    log(f"Epoch {epoch+1} - Train loss: {avg_loss:.4f}")

    # Validation
    model.eval()
    preds, targets = [], []
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=1)
            preds.extend(predictions.cpu().tolist())
            targets.extend(labels.cpu().tolist())

    val_f1 = f1_score(targets, preds, average="macro")
    report = classification_report(
        targets,
        preds,
        target_names=["Non Compliant", "Partially Compliant", "Compliant"],
    )
    log(f"Validation F1-score: {val_f1:.4f}")
    log(f"\nValidation Report:\n{report}")

    # Early stopping logic
    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        patience_counter = 0
        # Save the best model
        model.save_pretrained("saved_model")
        tokenizer.save_pretrained("saved_model")
        log("✅ New best model saved.")
    else:
        patience_counter += 1
        log(f"No improvement. Patience counter: {patience_counter}/{PATIENCE}")
        if patience_counter >= PATIENCE:
            log("⏹️ Early stopping triggered.")
            break

# Test evaluation
log("\n🔍 Evaluating on test set...")
model.eval()
test_preds, test_targets = [], []
with torch.no_grad():
    for batch in tqdm(test_loader, desc="Testing"):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids, attention_mask=attention_mask)
        predictions = torch.argmax(outputs.logits, dim=1)
        test_preds.extend(predictions.cpu().tolist())
        test_targets.extend(labels.cpu().tolist())

test_report = classification_report(
    test_targets,
    test_preds,
    target_names=["Non Compliant", "Partially Compliant", "Compliant"],
)
log(f"\nTest Report:\n{test_report}")

# Save test predictions
test_results = pd.DataFrame({"true_label": test_targets, "predicted_label": test_preds})
test_results_path = os.path.join("saved_model", "test_results.csv")
test_results.to_csv(test_results_path, index=False)
log(f"✅ Test results saved to {test_results_path}")
