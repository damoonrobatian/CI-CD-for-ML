"""CI preprocessing + training script for the drug classification project.

Loads data, fits a sklearn Pipeline (preprocessing + RandomForest), evaluates on
a held-out test set, then writes artifacts used by GitHub Actions (CML report) and
deployment (Gradio app on Hugging Face):

  - results/metrics.json       — accuracy and macro F1
  - results/confusion_matrix.png
  - model/model.skops          — full pipeline for inference (load + predict)
"""

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend for CI / headless runs
import matplotlib.pyplot as plt
import pandas as pd
import skops.io as sio
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

warnings.filterwarnings("ignore")

RESULTS_DIR = Path("results")
MODEL_DIR = Path("model")

# --- Data ---

drug_df = pd.read_csv("data/drug.csv").sample(frac=1, random_state=42)

X = drug_df.drop("Drug", axis=1)
y = drug_df["Drug"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- Preprocessing ---

cat_cols = ["Sex"]
ord_cols = ["BP", "Cholesterol"]
num_cols = ["Age", "Na_to_K"]

transform = ColumnTransformer(
    [
        (
            "ord_enc",
            OrdinalEncoder(
                categories=[
                    ["LOW", "NORMAL", "HIGH"],  # BP: explicit order, not alphabetical
                    ["NORMAL", "HIGH"],  # Cholesterol
                ]
            ),
            ord_cols,
        ),
        (
            "cat_enc",
            OneHotEncoder(handle_unknown="ignore"),
            cat_cols,
        ),
        (
            "num",
            # Impute then scale in sequence (see docs/setup-notes.md — tutorial pattern is wrong).
            Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            num_cols,
        ),
    ],
)

# Full pipeline: preprocessing + model saved together so inference needs only pipe.predict().
pipe = Pipeline(
    [
        ("preprocessing", transform),
        ("model", RandomForestClassifier(n_estimators=100, random_state=42)),
    ]
)

pipe.fit(X_train, y_train)

# --- Evaluation ---

y_pred = pipe.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average="macro")

print(f"Accuracy: {accuracy:.2f}")
print(classification_report(y_test, y_pred))

RESULTS_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

with open(RESULTS_DIR / "metrics.json", "w") as f:
    json.dump({"accuracy": accuracy, "f1_macro": f1}, f)

cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=pipe.classes_)
disp.plot()
plt.savefig(RESULTS_DIR / "confusion_matrix.png", dpi=120, bbox_inches="tight")
plt.close()

# skops saves the entire pipeline (encoders + model); app loads and calls predict only.
sio.dump(pipe, MODEL_DIR / "model.skops")
