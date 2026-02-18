"""
Language utilities - Detection, translation helpers
Optimized for rural Hindi/English users
"""

import re
from typing import Optional


def detect_language(text: str) -> str:
    """
    Detect if text is Hindi or English
    
    Returns:
        'hindi' or 'english'
    """
    # Check for Devanagari script (Hindi)
    hindi_chars = re.findall(r'[\u0900-\u097F]', text)
    
    if len(hindi_chars) > len(text) * 0.3:  # 30% Hindi characters
        return 'hindi'
    else:
        return 'english'


def romanize_hindi(text: str) -> str:
    """
    Convert Hindi numbers to English numbers
    Useful for parsing user input
    """
    hindi_to_english = {
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
        '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
    }
    
    for hindi, english in hindi_to_english.items():
        text = text.replace(hindi, english)
    
    return text


def extract_numbers(text: str) -> list:
    """
    Extract all numbers from text (handles Hindi/English)
    """
    text = romanize_hindi(text)
    numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text)
    return [float(n.replace(',', '')) for n in numbers]


def format_currency(amount: float, lang: str = 'hindi') -> str:
    """
    Format currency in Indian style
    
    Examples:
        25000 -> ₹25,000 (Hindi) or Rs. 25,000 (English)
        1000000 -> ₹10,00,000 (10 lakhs)
    """
    # Indian numbering system
    s = f"{amount:,.0f}"
    
    # Convert to Indian style (lakhs, crores)
    if amount >= 10000000:  # 1 crore
        formatted = f"{amount/10000000:.2f} करोड़" if lang == 'hindi' else f"{amount/10000000:.2f} Crore"
    elif amount >= 100000:  # 1 lakh
        formatted = f"{amount/100000:.2f} लाख" if lang == 'hindi' else f"{amount/100000:.2f} Lakh"
    else:
        formatted = f"₹{s}"
    
    return formatted


def simplify_banking_term(term: str, lang: str = 'hindi') -> Optional[str]:
    """
    Convert banking terms to simple language
    """
    terms_dict = {
        'emi': {
            'hindi': 'मासिक किस्त (हर महीने देनी होती है)',
            'english': 'Monthly Installment (payment every month)'
        },
        'interest rate': {
            'hindi': 'ब्याज दर (लोन पर अतिरिक्त पैसा)',
            'english': 'Interest Rate (extra money on loan)'
        },
        'credit score': {
            'hindi': 'क्रेडिट स्कोर (आपकी पैसे चुकाने की साख)',
            'english': 'Credit Score (your repayment trustworthiness)'
        },
        'tenure': {
            'hindi': 'अवधि (कितने महीने/साल में चुकाना है)',
            'english': 'Tenure (months/years to repay)'
        },
        'collateral': {
            'hindi': 'गिरवी (जमानत के तौर पर संपत्ति)',
            'english': 'Collateral (property as guarantee)'
        },
        'foreclosure': {
            'hindi': 'जल्दी चुकाना (समय से पहले पूरा लोन देना)',
            'english': 'Foreclosure (repaying loan early)'
        }
    }
    
    term_lower = term.lower()
    if term_lower in terms_dict:
        return terms_dict[term_lower].get(lang)
    
    return None


def get_regional_greeting(lang: str = 'hindi') -> str:
    """
    Get culturally appropriate greetings
    """
    greetings = {
        'hindi': '🙏 नमस्ते',
        'english': '👋 Hello',
        'punjabi': '🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ',
        'gujarati': '🙏 નમસ્તે',
        'marathi': '🙏 नमस्कार',
        'bengali': '🙏 নমস্কার'
    }
    
    return greetings.get(lang, greetings['hindi'])


def is_emergency_keyword(text: str) -> bool:
    """
    Detect if user needs urgent help (fraud, scam)
    """
    emergency_keywords = [
        'scam', 'fraud', 'cheat', 'fake', 'dhoka', 'धोखा', 
        'नकली', 'ठग', 'help', 'urgent', 'मदद', 'emergency'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in emergency_keywords)


# Test
if __name__ == "__main__":
    # Test language detection
    print(detect_language("मुद्रा योजना क्या है?"))  # hindi
    print(detect_language("What is Mudra Yojana?"))  # english
    
    # Test number extraction
    print(extract_numbers("मेरी आय ₹25,000 है"))  # [25000.0]
    
    # Test currency formatting
    print(format_currency(250000, 'hindi'))  # ₹2.50 लाख
    
    # Test term simplification
    print(simplify_banking_term('emi', 'hindi'))