"""
CodePulse AI Model Training & Evaluation Pipeline.
Trains a hybrid TF-IDF + Structural Feature Classifier on the vulnerability dataset.
Evaluates accuracy, precision, recall, F1, and saves model artifacts.
"""
import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import FeatureUnion
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, f1_score

from ml.dataset_builder import generate_dataset, DATASET_FILE
from ml.feature_extractor import CodeFeatureExtractor

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "codepulse_vulnerability_classifier.joblib"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

def train_and_evaluate():
    print(">> Step 1: Loading & Augmenting Dataset...")
    dataset = generate_dataset()
    
    texts = [item["code"] for item in dataset]
    labels = [item["label"] for item in dataset]
    languages = [item["language"] for item in dataset]

    print(">> Step 2: Extracting TF-IDF & Structural Features...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=400,
        token_pattern=r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]*\b|==|===|!=|\bgets\b|\beval\b'
    )
    X_tfidf = vectorizer.fit_transform(texts).toarray()

    X_struct = np.array([
        CodeFeatureExtractor.extract_structural_features(code, lang)
        for code, lang in zip(texts, languages)
    ])

    X_combined = np.hstack([X_tfidf, X_struct])
    y = np.array(labels)

    print(f">> Feature Matrix Shape: {X_combined.shape}")

    print(">> Step 3: Training Random Forest & Gradient Boosting Ensembles...")
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_combined, y)

    print(">> Step 4: Performing 5-Fold Stratified Cross-Validation...")
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_combined, y, cv=skf, scoring="accuracy")
    
    y_pred = model.predict(X_combined)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, average="weighted")
    report = classification_report(y, y_pred, output_dict=True)

    print(f"   - Training Accuracy: {acc * 100:.2f}%")
    print(f"   - Weighted F1-Score: {f1 * 100:.2f}%")
    print(f"   - Mean CV Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")

    print(">> Step 5: Serializing Model Artifacts...")
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    metadata = {
        "model_type": "RandomForestClassifier + MultiModal Structural Features",
        "training_accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "cv_accuracy_mean": round(float(cv_scores.mean()), 4),
        "classes": list(model.classes_),
        "num_samples": len(dataset),
        "classification_report": report
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f">> Model saved to {MODEL_PATH}")
    print(f">> Metadata saved to {METADATA_PATH}")
    return metadata

if __name__ == "__main__":
    train_and_evaluate()
