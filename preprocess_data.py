# preprocess.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
import json

# Define paths
data_path = "updated_compliance_dataset.csv"
output_dir = "./"
os.makedirs(output_dir, exist_ok=True)

# Load the dataset
df = pd.read_csv(data_path)

# Check for na
print("Rows with NA:", df.isnull().any(axis=1).sum())

# Ensure rows have a target value
df = df[df["Compliance Status"].notna()]

# Assert that there are 23 unique control IDs
controls_full = set(df["control_id"].unique())
assert (
    len(controls_full) == 23
), f"Expected 23 controls, but found {len(controls_full)}: {controls_full}"

# Build the text feature by concatenating the required columns
# Note: 'Implementation Details' and 'Recommendations' are excluded as requested.
df["text"] = (
    "[CONTROL_ID] "
    + df["control_id"].fillna("")
    + " [TITLE] "
    + df["title"].fillna("")
    + " [DESCRIPTION] "
    + df["description"].fillna("")
    + " [MEASURES] "
    + df["Current Measures"].fillna("")
)

# Label encode the target variable (Compliance Status)
label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df["Compliance Status"])
# right after label_encoder.fit_transform(...)
print("Label classes (in order):", label_encoder.classes_)
# Save the mapping (label classes) for future inference
model_dir = "model"
os.makedirs(model_dir, exist_ok=True)
with open(os.path.join(model_dir, "label_classes.json"), "w") as f:
    json.dump(label_encoder.classes_.tolist(), f)

# Split the dataset using stratification based on control_id
# Ensure all splits have rows for every control
train_df, temp_df = train_test_split(
    df, test_size=0.3, stratify=df["control_id"], random_state=42
)

val_df, test_df = train_test_split(
    temp_df, test_size=0.5, stratify=temp_df["control_id"], random_state=42
)

# Verify that each split has all 23 controls
for name, subset in zip(["Train", "Validation", "Test"], [train_df, val_df, test_df]):
    present = set(subset["control_id"].unique())
    print(f"{name} split contains {len(present)} controls: {present}")

# Save the splits with only the 'text' and 'label' columns
train_df[["text", "label"]].to_csv(os.path.join(output_dir, "train.csv"), index=False)
val_df[["text", "label"]].to_csv(os.path.join(output_dir, "val.csv"), index=False)
test_df[["text", "label"]].to_csv(os.path.join(output_dir, "test.csv"), index=False)

print("✅ Preprocessing complete. Files saved in the 'data' folder.")
