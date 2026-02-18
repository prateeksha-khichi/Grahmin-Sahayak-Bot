"""
Telegram Bot - CORRECTED Loan Handler
Asks the RIGHT questions for the actual model
"""

import os
import sys
import asyncio
from pathlib import Path

# ✅ ADD PROJECT ROOT TO PATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.error import NetworkError, TimedOut, BadRequest
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# ✅ Import services AFTER path setup
from services.rag_service import RAGService
from services.loan_service import LoanService
from services.fraud_service import FraudService
from services.advisory_service import AdvisoryService
from services.translation_service import TranslationService
from services.gtts_service import GTTsService
from services.ocr_service import OCRService
from database.db import SessionLocal, init_db
from database.models import UserPreference

# ✅ Initialize database first
try:
    init_db()
    logger.success("✅ Database initialized")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")

# ✅ Initialize services
try:
    rag_service = RAGService()
    loan_service = LoanService()
    fraud_service = FraudService()
    advisory_service = AdvisoryService()
    translation_service = TranslationService()
    gtts_service = GTTsService()
    ocr_service = OCRService()
    logger.success("✅ All services initialized")
except Exception as e:
    logger.error(f"⚠️ Some services failed to initialize: {e}")

# Conversation states
LANGUAGE_SELECT, LOCATION_INPUT = range(2)

# ✅ CORRECTED LOAN STATES (11 questions to match model features)
(LOAN_EDUCATION, LOAN_EMPLOYMENT, LOAN_DEPENDENTS, LOAN_INCOME,
 LOAN_AMOUNT, LOAN_TERM, LOAN_CREDIT, LOAN_RESIDENTIAL,
 LOAN_COMMERCIAL, LOAN_LUXURY, LOAN_BANK) = range(10, 21)

# ✅ FRAUD STATES
FRAUD_SCHEME_NAME, FRAUD_DESCRIPTION, FRAUD_SOURCE = range(30, 33)

# Language mappings
LANGUAGE_MAP = {
    'English': 'en',
    'Hindi': 'hi',
    'हिंदी': 'hi',
    'ਪੰਜਾਬੀ / Punjabi': 'pa',
    'Punjabi': 'pa',
    'മലയാളം / Malayalam': 'ml',
    'தமிழ் / Tamil': 'ta',
}

LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'Hindi',
    'pa': 'Punjabi',
    'ml': 'Malayalam',
    'ta': 'Tamil'
}


# ==================== ERROR HANDLER ==================== #

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for the bot"""
    
    logger.error(f"Exception while handling update: {context.error}")
    
    if isinstance(context.error, NetworkError):
        logger.warning("⚠️ Network error - retrying in 5 seconds...")
        await asyncio.sleep(5)
        return
    
    if isinstance(context.error, TimedOut):
        logger.warning("⚠️ Request timed out - retrying...")
        await asyncio.sleep(3)
        return
    
    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "❌ कुछ गड़बड़ी हुई। कृपया फिर से कोशिश करें\n"
                "❌ Something went wrong. Please try again"
            )
        except:
            pass


# ==================== HELPER FUNCTIONS ==================== #

def get_user_language(telegram_id: str) -> str:
    """Get user's preferred language from database"""
    db = SessionLocal()
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.telegram_user_id == telegram_id
        ).first()
        
        if pref and pref.preferred_language:
            return pref.preferred_language
        return 'hi'
    except Exception as e:
        logger.error(f"Error getting user language: {e}")
        return 'hi'
    finally:
        db.close()


# ==================== COMMAND HANDLERS ==================== #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    messages = {
        'en': f"""👋 Hello {update.effective_user.first_name}!

I am Gramin Sahayak Bot 🏦

Main Services:
🏦 /loan – Check loan eligibility
⚠️ /fraud – Detect fraud schemes
🔍 /schemes – Government schemes info

New Features:
📄 /explain – Explain bank documents
🌍 /language – Choose language
📢 /advisory – Daily advice

Ask anything or send voice message! 🎤""",

        'hi': f"""🙏 नमस्ते {update.effective_user.first_name}!

मैं ग्रामीण सहायक हूँ 🏦

मुख्य सेवाएं:
🏦 /loan – लोन पात्रता जांच
⚠️ /fraud – धोखाधड़ी जांच
🔍 /schemes – सरकारी योजनाएं

नई सुविधाएं:
📄 /explain – बैंक डॉक्यूमेंट समझाएं
🌍 /language – भाषा चुनें
📢 /advisory – आज की सलाह सुनें

कोई भी सवाल पूछें या आवाज़ में बोलें! 🎤""",

        'pa': f"""🙏 ਸਤ ਸ੍ਰੀ ਅਕਾਲ {update.effective_user.first_name}!

ਮੈਂ ਗ੍ਰਾਮੀਣ ਸਹਾਇਕ ਹਾਂ 🏦

ਮੁੱਖ ਸੇਵਾਵਾਂ:
🏦 /loan – ਲੋਨ ਯੋਗਤਾ ਜਾਂਚ
⚠️ /fraud – ਧੋਖਾਧੜੀ ਜਾਂਚ
🔍 /schemes – ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ

ਨਵੀਆਂ ਸੁਵਿਧਾਵਾਂ:
📄 /explain – ਬੈਂਕ ਦਸਤਾਵੇਜ਼ ਸਮਝਾਓ
🌍 /language – ਭਾਸ਼ਾ ਚੁਣੋ
📢 /advisory – ਅੱਜ ਦੀ ਸਲਾਹ

ਕੋਈ ਵੀ ਸਵਾਲ ਪੁੱਛੋ! 🎤"""
    }
    
    message = messages.get(user_lang, messages['hi'])
    await update.message.reply_text(message)


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command"""
    
    keyboard = [
        ['English', 'हिंदी / Hindi'],
        ['ਪੰਜਾਬੀ / Punjabi', 'മലയാളം / Malayalam'],
        ['தமிழ் / Tamil']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "🌍 Choose your language / अपनी भाषा चुनें:",
        reply_markup=reply_markup
    )
    
    return LANGUAGE_SELECT


async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    
    telegram_id = str(update.effective_user.id)
    selected = update.message.text
    
    lang_code = LANGUAGE_MAP.get(selected, 'hi')
    
    db = SessionLocal()
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.telegram_user_id == telegram_id
        ).first()
        
        if pref:
            pref.preferred_language = lang_code
        else:
            pref = UserPreference(
                telegram_user_id=telegram_id,
                preferred_language=lang_code
            )
            db.add(pref)
        
        db.commit()
        context.user_data['selected_language'] = lang_code
        
        messages = {
            'en': f"✅ Language selected: {LANGUAGE_NAMES.get(lang_code)}\n\nNow enter your city/district:\nExample: Jaipur, Delhi, Lucknow",
            'hi': f"✅ भाषा चुनी गई: {LANGUAGE_NAMES.get(lang_code)}\n\nअब अपना शहर/जिला बताएं:\nउदाहरण: जयपुर, दिल्ली, लखनऊ",
            'pa': f"✅ ਭਾਸ਼ਾ ਚੁਣੀ: {LANGUAGE_NAMES.get(lang_code)}\n\nਹੁਣ ਆਪਣਾ ਸ਼ਹਿਰ ਦੱਸੋ:\nਉਦਾਹਰਨ: Jaipur, Delhi"
        }
        
        message = messages.get(lang_code, messages['hi'])
        
        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
        
        return LOCATION_INPUT
        
    except Exception as e:
        logger.error(f"Error saving language: {e}")
        await update.message.reply_text("❌ Error saving language. Please try again.")
        return ConversationHandler.END
    finally:
        db.close()


async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location input"""
    
    telegram_id = str(update.effective_user.id)
    location = update.message.text
    lang_code = context.user_data.get('selected_language', 'hi')
    
    db = SessionLocal()
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.telegram_user_id == telegram_id
        ).first()
        
        if pref:
            pref.location = location
            pref.advisory_enabled = True
            db.commit()
        
        messages = {
            'en': f"""✅ Setup Complete!

Language: {LANGUAGE_NAMES.get(lang_code)}
Location: {location}

You will now receive daily voice advice every morning! 📢

/advisory - Listen now""",

            'hi': f"""✅ सेटिंग पूरी हुई!

भाषा: {LANGUAGE_NAMES.get(lang_code)}
जगह: {location}

अब आपको रोज़ सुबह आवाज़ में सलाह मिलेगी! 📢

/advisory - अभी सुनें""",

            'pa': f"""✅ ਸੈਟਅੱਪ ਪੂਰਾ!

ਭਾਸ਼ਾ: {LANGUAGE_NAMES.get(lang_code)}
ਸਥਾਨ: {location}

ਹੁਣ ਤੁਹਾਨੂੰ ਰੋਜ਼ ਸਲਾਹ ਮਿਲੇਗੀ! 📢

/advisory - ਹੁਣੇ ਸੁਣੋ""" 
        }
        
        message = messages.get(lang_code, messages['hi'])
        await update.message.reply_text(message)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error saving location: {e}")
        await update.message.reply_text("❌ Error saving location. Please try again.")
        return ConversationHandler.END
    finally:
        db.close()


async def advisory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /advisory command"""
    
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    db = SessionLocal()
    try:
        pref = db.query(UserPreference).filter(
            UserPreference.telegram_user_id == telegram_id
        ).first()
        
        if not pref:
            messages = {
                'en': "⚠️ Please set your language first using /language",
                'hi': "⚠️ कृपया पहले /language से भाषा चुनें",
                'pa': "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਪਹਿਲਾਂ /language ਨਾਲ ਭਾਸ਼ਾ ਚੁਣੋ"
            }
            await update.message.reply_text(messages.get(user_lang, messages['hi']))
            return
        
        location = pref.location or "Delhi"
        
        processing_messages = {
            'en': "📢 Preparing today's advice...",
            'hi': "📢 आज की सलाह तैयार कर रहा हूँ...",
            'pa': "📢 ਅੱਜ ਦੀ ਸਲਾਹ ਤਿਆਰ ਕਰ ਰਿਹਾ ਹਾਂ..."
        }
        
        await update.message.reply_text(processing_messages.get(user_lang, processing_messages['hi']))
        
        advisory_text = await advisory_service.generate_daily_advisory(telegram_id, location)
        
        if user_lang not in ['hi', 'en']:
            try:
                advisory_text = translation_service.translate(advisory_text, user_lang)
            except Exception as e:
                logger.error(f"Translation error: {e}")
        
        await update.message.reply_text(advisory_text)
        
        try:
            audio_path = gtts_service.text_to_speech(advisory_text, lang=user_lang)
            
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(
                    audio=audio,
                    caption="🎧 आवाज़ में सुनें / Listen in voice"
                )
            
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
        
    except Exception as e:
        logger.error(f"Advisory error: {e}")
        
        error_messages = {
            'en': "❌ Error occurred. Please try again later.",
            'hi': "❌ समस्या हुई। बाद में कोशिश करें",
            'pa': "❌ ਗਲਤੀ ਹੋਈ। ਬਾਅਦ ਵਿੱਚ ਕੋਸ਼ਿਸ਼ ਕਰੋ"
        }
        
        await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))
        
    finally:
        db.close()


async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /explain command"""
    
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    messages = {
        'en': """📄 Document Explanation Service

Please send:
- Bank letter (PDF)
- Loan rejection letter
- EMI schedule
- Passbook photo (Image)

I will explain it in simple language and voice! 🎧""",

        'hi': """📄 डॉक्यूमेंट समझाने वाली सेवा

कृपया भेजें:
- बैंक की चिट्ठी (PDF)
- लोन रिजेक्शन लेटर
- EMI शेड्यूल
- पासबुक की फोटो

मैं उसे आसान भाषा में समझाऊंगा और आवाज़ में बताऊंगा! 🎧""",

        'pa': """📄 ਦਸਤਾਵੇਜ਼ ਸਮਝਾਉਣ ਦੀ ਸੇਵਾ

ਕਿਰਪਾ ਕਰਕੇ ਭੇਜੋ:
- ਬੈਂਕ ਦੀ ਚਿੱਠੀ
- ਲੋਨ ਰਿਜੈਕਸ਼ਨ ਲੈਟਰ
- EMI ਸ਼ਿਡਿਊਲ

ਮੈਂ ਇਸਨੂੰ ਸੌਖੀ ਭਾਸ਼ਾ ਵਿੱਚ ਸਮਝਾਵਾਂਗਾ! 🎧"""
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))


async def schemes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schemes command"""
    
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    messages = {
        'en': """🏛️ Government Schemes

1️⃣ Mudra Yojana – Up to ₹10L
2️⃣ Kisan Credit Card
3️⃣ Stand Up India
4️⃣ PM-KISAN Yojana
5️⃣ Pradhan Mantri Awas Yojana

Ask about any scheme!""",

        'hi': """🏛️ सरकारी योजनाएं

1️⃣ मुद्रा योजना – ₹10L तक
2️⃣ किसान क्रेडिट कार्ड
3️⃣ स्टैंड अप इंडिया
4️⃣ PM-KISAN योजना
5️⃣ प्रधानमंत्री आवास योजना

किसी योजना के बारे में पूछें!""",

        'pa': """🏛️ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ

1️⃣ ਮੁਦਰਾ ਯੋਜਨਾ – ₹10L ਤੱਕ
2️⃣ ਕਿਸਾਨ ਕ੍ਰੈਡਿਟ ਕਾਰਡ
3️⃣ ਸਟੈਂਡ ਅੱਪ ਇੰਡੀਆ

ਕਿਸੇ ਵੀ ਯੋਜਨਾ ਬਾਰੇ ਪੁੱਛੋ!"""
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))


# ==================== LOAN HANDLERS ==================== #

async def loan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /loan command - START with education"""
    
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['loan_data'] = {}
    
    messages = {
        'en': """🏦 Loan Eligibility Check

I will ask you 11 questions to check your loan eligibility.

1️⃣ Education?
Type: Graduate or Not Graduate

/cancel to stop""",

        'hi': """🏦 लोन पात्रता जांच

मैं 11 सवाल पूछूंगा आपकी लोन पात्रता जांचने के लिए

1️⃣ शिक्षा?
टाइप करें: Graduate या Not Graduate

/cancel रद्द करने के लिए""",

        'pa': """🏦 ਲੋਨ ਯੋਗਤਾ ਜਾਂਚ

ਮੈਂ 11 ਸਵਾਲ ਪੁੱਛਾਂਗਾ

1️⃣ ਸਿੱਖਿਆ?
ਟਾਈਪ ਕਰੋ: Graduate ਜਾਂ Not Graduate

/cancel ਰੱਦ ਕਰਨ ਲਈ"""
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_EDUCATION


async def loan_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['loan_data']['education'] = update.message.text
    
    messages = {
        'en': f"✅ Education: {update.message.text}\n\n2️⃣ Self Employed?\nType: Yes or No",
        'hi': f"✅ शिक्षा: {update.message.text}\n\n2️⃣ खुद का व्यवसाय?\nटाइप करें: Yes या No",
        'pa': f"✅ ਸਿੱਖਿਆ: {update.message.text}\n\n2️⃣ ਖੁਦ ਦਾ ਕਾਰੋਬਾਰ?\nਟਾਈਪ ਕਰੋ: Yes ਜਾਂ No"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_EMPLOYMENT


async def loan_employment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['loan_data']['self_employed'] = update.message.text
    
    messages = {
        'en': f"✅ Self Employed: {update.message.text}\n\n3️⃣ Number of Dependents?\nHow many people depend on you?\nType: 0, 1, 2, 3, 4...",
        'hi': f"✅ रोजगार: {update.message.text}\n\n3️⃣ आश्रित?\nकितने लोग आप पर निर्भर हैं?\nटाइप करें: 0, 1, 2, 3, 4...",
        'pa': f"✅ ਰੁਜ਼ਗਾਰ: {update.message.text}\n\n3️⃣ ਨਿਰਭਰ?\nਕਿੰਨੇ ਲੋਕ?\nਟਾਈਪ ਕਰੋ: 0, 1, 2, 3..."
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_DEPENDENTS


async def loan_dependents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        dependents = int(update.message.text)
        context.user_data['loan_data']['no_of_dependents'] = dependents
    except:
        await update.message.reply_text("❌ Please enter a valid number")
        return LOAN_DEPENDENTS
    
    messages = {
        'en': f"✅ Dependents: {dependents}\n\n4️⃣ Annual Income (in ₹)?\nExample: 600000",
        'hi': f"✅ आश्रित: {dependents}\n\n4️⃣ वार्षिक आय (₹ में)?\nउदाहरण: 600000",
        'pa': f"✅ ਨਿਰਭਰ: {dependents}\n\n4️⃣ ਸਾਲਾਨਾ ਆਮਦਨ (₹ ਵਿੱਚ)?\nਉਦਾਹਰਨ: 600000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_INCOME


async def loan_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        income = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['income_annum'] = income
    except:
        await update.message.reply_text("❌ Please enter a valid number")
        return LOAN_INCOME
    
    messages = {
        'en': f"✅ Annual Income: ₹{income:,.0f}\n\n5️⃣ Loan Amount Needed (in ₹)?\nExample: 4000000",
        'hi': f"✅ वार्षिक आय: ₹{income:,.0f}\n\n5️⃣ कितना लोन चाहिए (₹ में)?\nउदाहरण: 4000000",
        'pa': f"✅ ਸਾਲਾਨਾ ਆਮਦਨ: ₹{income:,.0f}\n\n5️⃣ ਕਿੰਨਾ ਲੋਨ (₹ ਵਿੱਚ)?\nਉਦਾਹਰਨ: 4000000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_AMOUNT


async def loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        amount = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['loan_amount'] = amount
    except:
        await update.message.reply_text("❌ Please enter a valid amount")
        return LOAN_AMOUNT

    # ✅ FIXED: Ask for years (2-20), not months
    # Model was trained with loan_term in YEARS (range 2-20)
    messages = {
        'en': f"✅ Loan Amount: ₹{amount:,.0f}\n\n6️⃣ Loan Term (in years)?\nExample: 5, 10, 15, 20",
        'hi': f"✅ लोन राशि: ₹{amount:,.0f}\n\n6️⃣ लोन अवधि (सालों में)?\nउदाहरण: 5, 10, 15, 20",
        'pa': f"✅ ਲੋਨ ਰਕਮ: ₹{amount:,.0f}\n\n6️⃣ ਲੋਨ ਮਿਆਦ (ਸਾਲਾਂ ਵਿੱਚ)?\nਉਦਾਹਰਨ: 5, 10, 15, 20"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_TERM


async def loan_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        term = int(update.message.text)
        # ✅ FIXED: Accept years (2-20), convert to months for EMI display later
        if term < 1 or term > 30:
            raise ValueError()
        # Store as months internally so loan_service._calculate_loan_details works correctly
        # loan_service._prepare_features will convert months→years for the model
        context.user_data['loan_data']['loan_term'] = term * 12
    except:
        await update.message.reply_text("❌ Please enter years between 1 and 30")
        return LOAN_TERM
    
    messages = {
        'en': f"✅ Loan Term: {term} years\n\n7️⃣ CIBIL/Credit Score?\n300-900, if unknown type 650",
        'hi': f"✅ अवधि: {term} साल\n\n7️⃣ CIBIL/क्रेडिट स्कोर?\n300-900, नहीं पता तो 650 टाइप करें",
        'pa': f"✅ ਮਿਆਦ: {term} ਸਾਲ\n\n7️⃣ CIBIL ਸਕੋਰ?\n300-900, ਨਹੀਂ ਪਤਾ ਤਾਂ 650"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_CREDIT


async def loan_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        credit = int(update.message.text)
        if credit < 300 or credit > 900:
            raise ValueError()
        context.user_data['loan_data']['cibil_score'] = credit
    except:
        await update.message.reply_text("❌ Please enter a number between 300-900")
        return LOAN_CREDIT
    
    messages = {
        'en': f"✅ CIBIL Score: {credit}\n\n8️⃣ Residential Assets Value (in ₹)?\nHome/Plot value, 0 if none\nExample: 2000000",
        'hi': f"✅ CIBIL स्कोर: {credit}\n\n8️⃣ आवासीय संपत्ति का मूल्य (₹)?\nघर/प्लॉट, नहीं है तो 0\nउदाहरण: 2000000",
        'pa': f"✅ CIBIL ਸਕੋਰ: {credit}\n\n8️⃣ ਰਿਹਾਇਸ਼ੀ ਜਾਇਦਾਦ (₹)?\nਘਰ/ਜ਼ਮੀਨ, 0 ਜੇ ਨਹੀਂ\nਉਦਾਹਰਨ: 2000000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_RESIDENTIAL


async def loan_residential(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        res_assets = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['residential_assets_value'] = res_assets
    except:
        await update.message.reply_text("❌ Please enter a valid amount or 0")
        return LOAN_RESIDENTIAL
    
    messages = {
        'en': f"✅ Residential Assets: ₹{res_assets:,.0f}\n\n9️⃣ Commercial Assets Value (in ₹)?\nShop/Office, 0 if none\nExample: 500000",
        'hi': f"✅ आवासीय संपत्ति: ₹{res_assets:,.0f}\n\n9️⃣ व्यावसायिक संपत्ति (₹)?\nदुकान/ऑफिस, नहीं है तो 0\nउदाहरण: 500000",
        'pa': f"✅ ਰਿਹਾਇਸ਼ੀ: ₹{res_assets:,.0f}\n\n9️⃣ ਵਪਾਰਕ ਜਾਇਦਾਦ (₹)?\nਦੁਕਾਨ/ਦਫਤਰ, 0 ਜੇ ਨਹੀਂ\nਉਦਾਹਰਨ: 500000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_COMMERCIAL


async def loan_commercial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        com_assets = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['commercial_assets_value'] = com_assets
    except:
        await update.message.reply_text("❌ Please enter a valid amount or 0")
        return LOAN_COMMERCIAL
    
    messages = {
        'en': f"✅ Commercial Assets: ₹{com_assets:,.0f}\n\n🔟 Luxury Assets Value (in ₹)?\nCar/Bike/Jewelry, 0 if none\nExample: 300000",
        'hi': f"✅ व्यावसायिक संपत्ति: ₹{com_assets:,.0f}\n\n🔟 लक्जरी संपत्ति (₹)?\nकार/बाइक/ज्वेलरी, नहीं है तो 0\nउदाहरण: 300000",
        'pa': f"✅ ਵਪਾਰਕ: ₹{com_assets:,.0f}\n\n🔟 ਲਗਜ਼ਰੀ ਜਾਇਦਾਦ (₹)?\nਕਾਰ/ਬਾਈਕ, 0 ਜੇ ਨਹੀਂ\nਉਦਾਹਰਨ: 300000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_LUXURY


async def loan_luxury(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        lux_assets = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['luxury_assets_value'] = lux_assets
    except:
        await update.message.reply_text("❌ Please enter a valid amount or 0")
        return LOAN_LUXURY
    
    messages = {
        'en': f"✅ Luxury Assets: ₹{lux_assets:,.0f}\n\n1️⃣1️⃣ Bank Assets Value (in ₹)?\nSavings/FD/Deposits, 0 if none\nExample: 100000",
        'hi': f"✅ लक्जरी संपत्ति: ₹{lux_assets:,.0f}\n\n1️⃣1️⃣ बैंक में जमा (₹)?\nSavings/FD/Deposits, नहीं है तो 0\nउदाहरण: 100000",
        'pa': f"✅ ਲਗਜ਼ਰੀ: ₹{lux_assets:,.0f}\n\n1️⃣1️⃣ ਬੈਂਕ ਜਮ੍ਹਾਂ (₹)?\nSavings/FD, 0 ਜੇ ਨਹੀਂ\nਉਦਾਹਰਨ: 100000"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return LOAN_BANK


async def loan_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Final step - get bank assets and make prediction"""
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    try:
        bank_assets = float(update.message.text.replace(',', ''))
        context.user_data['loan_data']['bank_asset_value'] = bank_assets
    except:
        await update.message.reply_text("❌ Please enter a valid amount or 0")
        return LOAN_BANK
    
    processing_messages = {
        'en': "⏳ Checking your eligibility...",
        'hi': "⏳ जांच हो रही है...",
        'pa': "⏳ ਜਾਂਚ ਹੋ ਰਹੀ ਹੈ..."
    }
    
    await update.message.reply_text(processing_messages.get(user_lang, processing_messages['hi']))
    
    try:
        loan_data = context.user_data['loan_data']
        result = loan_service.predict_eligibility(loan_data)
        
        message = result['message_hindi'] if user_lang == 'hi' else result['message_english']
        
        if user_lang not in ['hi', 'en']:
            try:
                message = translation_service.translate(message, user_lang)
            except:
                pass
        
        await update.message.reply_text(message)
        context.user_data.pop('loan_data', None)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Loan prediction error: {e}")
        
        error_messages = {
            'en': "❌ Error checking eligibility. Please try again with /loan",
            'hi': "❌ जांच में समस्या हुई। कृपया /loan से फिर प्रयास करें",
            'pa': "❌ ਗਲਤੀ ਹੋਈ। /loan ਨਾਲ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ"
        }
        
        await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))
        context.user_data.pop('loan_data', None)
        return ConversationHandler.END


# ==================== FRAUD HANDLERS ==================== #

async def fraud_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['fraud_data'] = {}
    
    messages = {
        'en': """🔍 Fraud Detection Service

I will help you check if a loan scheme is genuine or fake.

1️⃣ Scheme Name?
Type the name of the loan/scheme

/cancel to stop""",

        'hi': """🔍 धोखाधड़ी जांच सेवा

मैं जांच करूंगा कि लोन योजना असली है या नकली

1️⃣ योजना का नाम?
योजना का नाम टाइप करें

/cancel रद्द करने के लिए""",

        'pa': """🔍 ਧੋਖਾਧੜੀ ਜਾਂਚ

ਮੈਂ ਜਾਂਚ ਕਰਾਂਗਾ

1️⃣ ਯੋਜਨਾ ਦਾ ਨਾਮ?

/cancel ਰੱਦ ਕਰਨ ਲਈ"""
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return FRAUD_SCHEME_NAME


async def fraud_scheme_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['fraud_data']['scheme_name'] = update.message.text
    
    messages = {
        'en': f"✅ Scheme: {update.message.text}\n\n2️⃣ Description?\nWhat promises are being made?",
        'hi': f"✅ योजना: {update.message.text}\n\n2️⃣ विवरण?\nक्या वादे किए जा रहे हैं?",
        'pa': f"✅ ਯੋਜਨਾ: {update.message.text}\n\n2️⃣ ਵੇਰਵਾ?\nਕੀ ਵਾਅਦੇ ਹਨ?"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return FRAUD_DESCRIPTION


async def fraud_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['fraud_data']['description'] = update.message.text
    
    messages = {
        'en': f"✅ Description saved\n\n3️⃣ Source?\nWhere did you hear about this?\nExample: WhatsApp, Website, Agent",
        'hi': f"✅ विवरण सहेजा गया\n\n3️⃣ स्रोत?\nआपको कहां से पता चला?\nउदाहरण: WhatsApp, Website, Agent",
        'pa': f"✅ ਵੇਰਵਾ ਸੁਰੱਖਿਅਤ\n\n3️⃣ ਸਰੋਤ?\nਤੁਹਾਨੂੰ ਕਿੱਥੋਂ ਪਤਾ ਲੱਗਾ?\nਉਦਾਹਰਨ: WhatsApp"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return FRAUD_SOURCE


async def fraud_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data['fraud_data']['source'] = update.message.text
    context.user_data['fraud_data']['contact'] = ""
    
    processing_messages = {
        'en': "🔍 Checking for fraud signals...",
        'hi': "🔍 धोखाधड़ी के संकेत जांच रहे हैं...",
        'pa': "🔍 ਧੋਖਾਧੜੀ ਦੇ ਸੰਕੇਤ ਜਾਂਚ ਰਹੇ ਹਾਂ..."
    }
    
    await update.message.reply_text(processing_messages.get(user_lang, processing_messages['hi']))
    
    try:
        fraud_data = context.user_data['fraud_data']
        result = fraud_service.detect_fraud(fraud_data)
        
        message = result['warning_message_hindi'] if user_lang == 'hi' else result['warning_message_english']
        
        if user_lang not in ['hi', 'en']:
            try:
                message = translation_service.translate(message, user_lang)
            except:
                pass
        
        await update.message.reply_text(message)
        context.user_data.pop('fraud_data', None)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Fraud detection error: {e}")
        
        error_messages = {
            'en': "❌ Error checking fraud. Please try again with /fraud",
            'hi': "❌ जांच में समस्या हुई। कृपया /fraud से फिर प्रयास करें",
            'pa': "❌ ਗਲਤੀ ਹੋਈ। /fraud ਨਾਲ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ"
        }
        
        await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))
        context.user_data.pop('fraud_data', None)
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    
    context.user_data.clear()
    
    messages = {
        'en': "❌ Cancelled. Type /start to see available commands",
        'hi': "❌ रद्द किया गया। /start टाइप करें कमांड देखने के लिए",
        'pa': "❌ ਰੱਦ ਕੀਤਾ। /start ਟਾਈਪ ਕਰੋ"
    }
    
    await update.message.reply_text(messages.get(user_lang, messages['hi']))
    return ConversationHandler.END


# ==================== DOCUMENT & QUERY HANDLERS ==================== #

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    file_path = None
    
    try:
        if update.message.document:
            file = await update.message.document.get_file()
            file_ext = 'pdf'
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_ext = 'jpg'
        else:
            return
        
        file_path = f"temp_{telegram_id}.{file_ext}"
        await file.download_to_drive(file_path)
        
        extracted_text = ocr_service.extract_text(file_path, file_ext)
        
        if not extracted_text:
            error_messages = {
                'en': "❌ Could not extract text. Please try again",
                'hi': "❌ टेक्स्ट नहीं मिला। फिर कोशिश करें",
                'pa': "❌ ਟੈਕਸਟ ਨਹੀਂ ਮਿਲਿਆ"
            }
            await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))
            return
        
        lang_for_rag = 'hindi' if user_lang == 'hi' else 'english'
        
        simplified = rag_service.answer_question(
            f"Explain this document in simple language: {extracted_text[:1000]}",
            language=lang_for_rag
        )
        
        answer_text = simplified['answer']
        
        if user_lang not in ['hi', 'en']:
            try:
                answer_text = translation_service.translate(answer_text, user_lang)
            except Exception as e:
                logger.error(f"Translation error: {e}")
        
        await update.message.reply_text(answer_text)
        
        try:
            audio_path = gtts_service.text_to_speech(answer_text, lang=user_lang)
            
            with open(audio_path, 'rb') as audio:
                await update.message.reply_audio(audio=audio, caption="🎧 आवाज़ में सुनें")
            
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            logger.error(f"Audio generation error: {e}")
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        
        error_messages = {
            'en': "❌ Error processing document",
            'hi': "❌ डॉक्यूमेंट को समझने में समस्या हुई",
            'pa': "❌ ਦਸਤਾਵੇਜ਼ ਨੂੰ ਸਮਝਣ ਵਿੱਚ ਸਮੱਸਿਆ"
        }
        
        await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))
    
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


async def handle_text_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    user_lang = get_user_language(telegram_id)
    query = update.message.text
    
    try:
        lang_for_rag = 'hindi' if user_lang == 'hi' else 'english'
        result = rag_service.answer_question(query, language=lang_for_rag)
        answer = result['answer']
        
        if user_lang not in ['hi', 'en']:
            try:
                answer = translation_service.translate(answer, user_lang)
            except Exception as e:
                logger.error(f"Translation error: {e}")
        
        await update.message.reply_text(answer)
        
    except Exception as e:
        logger.error(f"Text query error: {e}")
        
        error_messages = {
            'en': "❌ Error processing query",
            'hi': "❌ प्रश्न संसाधित करने में त्रुटि",
            'pa': "❌ ਸਵਾਲ ਦਾ ਜਵਾਬ ਦੇਣ ਵਿੱਚ ਗਲਤੀ"
        }
        
        await update.message.reply_text(error_messages.get(user_lang, error_messages['hi']))


# ==================== MAIN ==================== #

def main():
    """Run the bot"""
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in .env file!")
        return
    
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        logger.success("✅ Internet connection verified")
    except OSError:
        logger.error("❌ No internet connection detected!")
        return
    
    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )
    
    application.add_error_handler(error_handler)
    
    # Language conversation handler
    lang_conv = ConversationHandler(
        entry_points=[CommandHandler('language', language_command)],
        states={
            LANGUAGE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_selected)],
            LOCATION_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # ✅ Loan conversation handler (11 steps)
    loan_conv = ConversationHandler(
        entry_points=[CommandHandler('loan', loan_command)],
        states={
            LOAN_EDUCATION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_education)],
            LOAN_EMPLOYMENT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_employment)],
            LOAN_DEPENDENTS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_dependents)],
            LOAN_INCOME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_income)],
            LOAN_AMOUNT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_amount)],
            LOAN_TERM:        [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_term)],
            LOAN_CREDIT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_credit)],
            LOAN_RESIDENTIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_residential)],
            LOAN_COMMERCIAL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_commercial)],
            LOAN_LUXURY:      [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_luxury)],
            LOAN_BANK:        [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_bank)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Fraud conversation handler
    fraud_conv = ConversationHandler(
        entry_points=[CommandHandler('fraud', fraud_command)],
        states={
            FRAUD_SCHEME_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fraud_scheme_name)],
            FRAUD_DESCRIPTION:  [MessageHandler(filters.TEXT & ~filters.COMMAND, fraud_description)],
            FRAUD_SOURCE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, fraud_source)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add all handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('advisory', advisory_command))
    application.add_handler(CommandHandler('explain', explain_command))
    application.add_handler(CommandHandler('schemes', schemes_command))
    application.add_handler(CommandHandler('cancel', cancel))
    
    application.add_handler(lang_conv)
    application.add_handler(loan_conv)
    application.add_handler(fraud_conv)
    
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_document))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_query))
    
    logger.success("=" * 60)
    logger.success("🤖 Telegram Bot Starting...")
    logger.success("=" * 60)
    
    try:
        logger.info("Connecting to Telegram servers...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")


if __name__ == '__main__':
    main()