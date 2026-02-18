from pathlib import Path
from typing import Dict
import joblib
import numpy as np
import pandas as pd
from loguru import logger


class LoanService:
    """Loan eligibility prediction service"""

    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.model_dir = BASE_DIR / "models" / "loan_eligibility"
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            model_path = self.model_dir / "loan_eligibility_model.pkl"
            self.model = joblib.load(model_path)
            logger.success("✅ Loan model loaded")
            if hasattr(self.model, "feature_names_in_"):
                logger.info(f"📋 Model expects features: {list(self.model.feature_names_in_)}")
        except Exception as e:
            logger.exception(f"❌ Failed to load model: {e}")
            self.model = None

    def predict_eligibility(self, user_data: Dict) -> Dict:
        if self.model is None:
            return self._error_response("मॉडल लोड नहीं हो पाया")

        try:
            logger.info("=" * 60)
            logger.info("LOAN PREDICTION")
            logger.info("=" * 60)

            features = self._prepare_features(user_data)

            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0]

            eligible = bool(prediction == 1)
            confidence = float(max(probability))

            logger.info(f"🎯 RESULT: {'✅ APPROVED' if eligible else '❌ REJECTED'} ({confidence:.1%})")

            loan_details = self._calculate_loan_details(user_data, eligible)

            result = {
                "eligible": eligible,
                "confidence": round(confidence, 2),
                "recommended_amount": loan_details["recommended_amount"],
                "emi": loan_details["emi"],
                "interest_rate": loan_details["interest_rate"],
                "tenure_months": loan_details["tenure_months"],
            }

            messages = self._generate_messages(eligible, result, user_data)
            result["message_hindi"] = messages["hindi"]
            result["message_english"] = messages["english"]

            return result

        except Exception as e:
            logger.exception(f"❌ Error: {e}")
            return self._error_response("आंतरिक त्रुटि")

    def _prepare_features(self, user_data: Dict) -> pd.DataFrame:
        dependents = int(user_data.get("no_of_dependents", 0))

        education_raw = str(user_data.get("education", "Graduate")).lower()
        education = 1 if "graduate" in education_raw else 0

        self_employed_raw = str(user_data.get("self_employed", "No")).lower()
        self_employed = 1 if "yes" in self_employed_raw else 0

        # IMPORTANT: Model was trained with loan_term in YEARS (range 2-20).
        # User inputs months (e.g. 180), so convert: months ÷ 12 = years.
        loan_term_input = float(user_data.get("loan_term", 12))
        loan_term_years = round(loan_term_input / 12) if loan_term_input > 20 else loan_term_input
        loan_term_years = max(2, min(20, loan_term_years))  # clamp to training range

        logger.info(f"📋 loan_term input={loan_term_input} → model value={loan_term_years} years")

        feature_dict = {
            "no_of_dependents":         dependents,
            "education":                education,
            "self_employed":            self_employed,
            "income_annum":             float(user_data.get("income_annum", 0)),
            "loan_amount":              float(user_data.get("loan_amount", 0)),
            "loan_term":                loan_term_years,
            "cibil_score":              float(user_data.get("cibil_score", 650)),
            "residential_assets_value": float(user_data.get("residential_assets_value", 0)),
            "commercial_assets_value":  float(user_data.get("commercial_assets_value", 0)),
            "luxury_assets_value":      float(user_data.get("luxury_assets_value", 0)),
            "bank_asset_value":         float(user_data.get("bank_asset_value", 0)),
        }

        # Reorder columns to exactly match model's training order
        if hasattr(self.model, "feature_names_in_"):
            expected_cols = list(self.model.feature_names_in_)
            feature_dict = {col: feature_dict[col] for col in expected_cols if col in feature_dict}

        return pd.DataFrame([feature_dict])

    def _calculate_loan_details(self, user_data: Dict, eligible: bool) -> Dict:
        requested = user_data.get("loan_amount", 0)
        income_annum = user_data.get("income_annum", 0)

        cibil = user_data.get("cibil_score", 650)
        if cibil >= 750:
            interest_rate = 8.5
        elif cibil >= 700:
            interest_rate = 10.0
        else:
            interest_rate = 12.0

        max_eligible = income_annum * 5
        recommended = min(requested, max_eligible) if eligible else 0

        # tenure for EMI is always in months (user's original input)
        tenure_months = float(user_data.get("loan_term", 12))
        if tenure_months <= 20:
            # User gave years, convert to months for EMI calc
            tenure_months = tenure_months * 12

        if recommended > 0 and tenure_months > 0:
            r = interest_rate / (12 * 100)
            n = tenure_months
            emi = recommended * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else recommended / n
        else:
            emi = 0

        return {
            "recommended_amount": round(recommended, 2),
            "emi": round(emi, 2),
            "interest_rate": interest_rate,
            "tenure_months": int(tenure_months),
        }

    def _generate_messages(self, eligible: bool, loan: Dict, user_data: Dict) -> Dict:
        if eligible:
            return {
                "hindi": (
                    f"✅ बधाई हो! आप लोन के लिए पात्र हैं\n\n"
                    f"💰 अनुमोदित राशि: ₹{loan['recommended_amount']:,.0f}\n"
                    f"📅 मासिक EMI: ₹{loan['emi']:,.0f}\n"
                    f"📊 ब्याज दर: {loan['interest_rate']}% प्रति वर्ष\n"
                    f"⏱ अवधि: {loan['tenure_months']} महीने\n\n"
                    f"💡 अगले कदम:\n"
                    f"1. नज़दीकी बैंक शाखा में जाएं\n"
                    f"2. आवश्यक दस्तावेज़ ले जाएं"
                ),
                "english": (
                    f"✅ Congratulations! You are eligible\n\n"
                    f"💰 Approved: ₹{loan['recommended_amount']:,.0f}\n"
                    f"📅 EMI: ₹{loan['emi']:,.0f}\n"
                    f"📊 Rate: {loan['interest_rate']}%\n"
                    f"⏱ Tenure: {loan['tenure_months']} months"
                ),
            }
        else:
            return {
                "hindi": (
                    "❌ आप वर्तमान में लोन के लिए पात्र नहीं हैं\n\n"
                    "📌 सुझाव:\n"
                    "• अपना CIBIL स्कोर 700+ तक बढ़ाएं\n"
                    "• संपत्ति का मूल्य बढ़ाएं\n"
                    "• छोटी राशि का लोन लें"
                ),
                "english": (
                    "❌ Not currently eligible\n\n"
                    "• Improve CIBIL to 700+\n"
                    "• Increase collateral\n"
                    "• Request smaller amount"
                ),
            }

    def _error_response(self, message: str) -> Dict:
        return {
            "eligible": False,
            "confidence": 0.0,
            "recommended_amount": 0.0,
            "emi": 0.0,
            "interest_rate": 0.0,
            "tenure_months": 0,
            "message_hindi": f"❌ त्रुटि: {message}",
            "message_english": f"❌ Error: {message}",
        }