import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
from typing import Dict, Any
from ml.feature_extractor import CodeFeatureExtractor

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
MODEL_PATH = MODEL_DIR / "codepulse_vulnerability_classifier.joblib"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

class MLVulnerabilityPredictor:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.classes = []
        self._load_artifacts()

    def _load_artifacts(self):
        if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                self.vectorizer = joblib.load(VECTORIZER_PATH)
                self.classes = list(self.model.classes_)
            except Exception:
                self.model = None

    def predict(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Predicts vulnerability category, probability, and risk factors.
        """
        if not self.model or not self.vectorizer:
            return {
                "status": "model_not_trained",
                "risk_score": 0.1,
                "predicted_label": "CLEAN_CODE",
                "probabilities": {}
            }

        try:
            tfidf_vec = self.vectorizer.transform([code]).toarray()
            struct_vec = CodeFeatureExtractor.extract_structural_features(code, language).reshape(1, -1)
            X = np.hstack([tfidf_vec, struct_vec])

            pred_label = self.model.predict(X)[0]
            probs = self.model.predict_proba(X)[0]
            prob_dict = {cls_name: round(float(p), 3) for cls_name, p in zip(self.classes, probs)}

            vuln_prob = prob_dict.get("SECURITY_VULNERABILITY", 0.0)
            complex_prob = prob_dict.get("COMPLEXITY_RISK", 0.0)
            
            risk_score = round(max(vuln_prob, complex_prob * 0.7), 2)

            return {
                "status": "success",
                "predicted_label": pred_label,
                "risk_score": risk_score,
                "probabilities": prob_dict,
                "model_type": "Random Forest ML Classifier"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "risk_score": 0.0,
                "predicted_label": "UNKNOWN"
            }
