"""
Fraud Detection Service - Detects fake loan schemes
"""

from pathlib import Path
import joblib
import re
from typing import Dict, List
from loguru import logger
import numpy as np  # ✅ ADD THIS


class FraudService:
    """
    Fraud detection for loan schemes
    """

    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.model_dir = BASE_DIR / "models" / "loan_eligibility"

        self.model = None
        self.vectorizer = None

        # Fraud keywords (Hindi + English)
        self.fraud_keywords = [
            "instant approval", "no documents", "guaranteed loan",
            "pay first", "advance fee", "processing fee upfront",
            "तुरंत स्वीकृति", "बिना दस्तावेज", "पक्की मंजूरी",
            "पहले पैसे दें", "एडवांस फीस", "प्रोसेसिंग शुल्क पहले",
            "100% approval", "no credit check", "urgent loan",
            "whatsapp loan", "telegram loan", "personal loan agent"
        ]

        # Government verified schemes
        self.verified_schemes = [
            "pradhan mantri mudra yojana",
            "kisan credit card",
            "stand up india",
            "प्रधानमंत्री मुद्रा योजना",
            "किसान क्रेडिट कार्ड",
            "स्टैंड अप इंडिया",
            "nabard",
            "sidbi",
            "pmegp",
            "shishu",
            "kishor",
            "tarun"
        ]

        self._load_model()

    def _load_model(self):
        """Load trained fraud detection model"""
        model_path = self.model_dir / "fraud_detector_model.pkl"
        vectorizer_path = self.model_dir / "fraud_vectorizer.pkl"

        if not model_path.exists() or not vectorizer_path.exists():
            logger.warning(
                f"⚠️  Fraud ML model not found at {self.model_dir}\n"
                f"Using rule-based detection only"
            )
            return

        try:
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            logger.success("✅ Fraud detection model loaded")

        except Exception as e:
            logger.exception(f"❌ Failed to load fraud model: {e}")
            self.model = None
            self.vectorizer = None

    def detect_fraud(self, scheme_data: Dict) -> Dict:
        """Detect if a scheme is fraudulent"""
        
        scheme_name = scheme_data.get("scheme_name", "").lower()
        description = scheme_data.get("description", "").lower()
        source = scheme_data.get("source", "").lower()
        contact = scheme_data.get("contact", "").lower()

        combined_text = f"{scheme_name} {description} {source} {contact}"

        # Verified scheme check
        is_verified = self._is_verified_scheme(scheme_name)

        # Rule-based signals
        fraud_signals = self._detect_fraud_signals(combined_text)

        # ML-based score
        ml_score = 0.0
        if self.model and self.vectorizer:
            try:
                vec = self.vectorizer.transform([combined_text])
                ml_score = float(self.model.predict_proba(vec)[0][1])
            except Exception as e:
                logger.error(f"ML fraud prediction failed: {e}")

        rule_score = min(len(fraud_signals) * 0.2, 1.0)
        final_score = max(ml_score, rule_score)

        is_fraud = final_score > 0.5 and not is_verified

        messages = self._generate_warning_messages(
            is_fraud, is_verified, fraud_signals, scheme_name
        )

        return {
            "is_fraud": is_fraud,
            "confidence": round(final_score, 2),
            "fraud_signals": fraud_signals,
            "warning_message_hindi": messages["hindi"],
            "warning_message_english": messages["english"],
            "verified": is_verified
        }

    def _is_verified_scheme(self, scheme_name: str) -> bool:
        """Check if scheme is government verified"""
        return any(v in scheme_name for v in self.verified_schemes)

    def _detect_fraud_signals(self, text: str) -> List[str]:
        """Detect fraud signals in text"""
        signals = []

        for keyword in self.fraud_keywords:
            if keyword in text:
                signals.append(keyword)

        # Suspicious contact pattern
        if re.search(r"\d{10}", text) and ("whatsapp" in text or "telegram" in text):
            signals.append("suspicious_contact_method")

        # Advance payment detection
        if re.search(r"(advance|एडवांस).*(₹|\d+)", text, re.IGNORECASE):
            signals.append("advance_payment_required")

        if "no verification" in text or "without verification" in text:
            signals.append("no_verification")

        return list(set(signals))

    def _generate_warning_messages(
        self,
        is_fraud: bool,
        is_verified: bool,
        fraud_signals: List[str],
        scheme_name: str
    ) -> Dict[str, str]:
        """Generate warning messages"""

        if is_verified:
            return {
                "hindi": (
                    f"✅ यह एक सत्यापित सरकारी योजना है: {scheme_name}\n\n"
                    f"🛡️ सुरक्षित:\n"
                    f"- सरकार द्वारा मान्यता प्राप्त\n"
                    f"- किसी भी बैंक से आवेदन करें\n"
                    f"- कोई एडवांस फीस नहीं"
                ),
                "english": (
                    f"✅ This is a verified government scheme: {scheme_name}\n\n"
                    f"🛡️ Safe:\n"
                    f"- Government recognized\n"
                    f"- Apply through any bank\n"
                    f"- No advance fees"
                ),
            }

        if is_fraud:
            signals = ", ".join(fraud_signals[:3])
            return {
                "hindi": (
                    "🚨 चेतावनी: यह योजना नकली हो सकती है!\n\n"
                    f"❌ संदेहजनक संकेत: {signals}\n\n"
                    "📞 शिकायत: साइबर क्राइम हेल्पलाइन 1930"
                ),
                "english": (
                    "🚨 WARNING: This scheme may be FAKE!\n\n"
                    f"❌ Suspicious signals: {signals}\n\n"
                    "📞 Report: Cyber Crime Helpline 1930"
                ),
            }

        return {
            "hindi": f"⚠️  योजना सत्यापित नहीं है: {scheme_name}\nकृपया आवेदन से पहले जांच करें",
            "english": f"⚠️  Scheme not verified: {scheme_name}\nPlease verify before applying",
        }