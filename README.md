# 🌾 Grahmin Sahayak Bot
### AI-Powered Rural Digital Assistant

> 💚 "Technology should reach villages before it reaches luxury."

Grahmin Sahayak Bot is an intelligent, multilingual rural assistance chatbot built to support villagers and farmers with financial guidance, loan eligibility, fraud awareness, and conversational AI — all through Telegram. The project focuses on bridging the digital divide by providing simple, voice-enabled, AI-driven access to financial and informational services for rural India.

---

## 🚩 Problem Statement

Rural communities often face:

- 📉 Lack of financial literacy
- 🏦 Difficulty accessing loan information
- ⚠️ Exposure to fraud
- 🗣️ Language barriers
- 📵 No easy digital interface for guidance
- 📋 Limited awareness of schemes and services

Most existing platforms are complex, English-heavy, or require technical knowledge.

---

## ✅ Our Solution

Grahmin Sahayak Bot provides:

- 💬 Natural chat-based interaction
- 🤖 Loan eligibility prediction using ML
- 🧮 EMI calculation
- 🌐 Multilingual support
- 🎙️ Voice input/output
- 🛡️ Fraud awareness
- 📚 RAG-based intelligent answers
- 🕐 24x7 automated assistance

All inside a familiar Telegram chat interface.

---

## ✨ Core Features — 6 Major Modules

### 1️⃣ AI Loan Eligibility System (ML)
- Predicts loan eligibility using trained Machine Learning models
- Calculates EMI instantly
- Uses realistic rural financial parameters

### 2️⃣ Multilingual Support
- Users can interact in multiple Indian languages
- Helps eliminate language barriers and improves accessibility

### 3️⃣ Voice Assistance
- 🎙️ Voice input from users
- 🔊 Voice responses from bot
- Designed for low-literacy users

### 4️⃣ Fraud Awareness Module
- Detects suspicious queries
- Educates users about safe borrowing
- Provides preventive financial advice

### 5️⃣ RAG (Retrieval Augmented Generation)
Provides intelligent responses using a custom knowledge base. Used for:
- FAQs
- Financial guidance
- Rural information
- Scheme awareness (future)

### 6️⃣ Telegram UI/UX Bot Interface
- Simple conversational UI
- Button-based navigation
- Minimal typing required
- Mobile friendly

---

## 🧠 RAG Architecture — Step by Step
```
User asks a question
        ↓
Query is embedded
        ↓
Relevant documents retrieved from vector database
        ↓
Context + query sent to LLM
        ↓
Final grounded response returned to user
```

This ensures:
- ✅ Accurate answers
- ✅ Reduced hallucination
- ✅ Context-aware replies

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python, FastAPI, REST APIs |
| Machine Learning | Scikit-learn, NumPy, Pandas, Custom ML Models |
| Database | PostgreSQL (Neon Cloud) |
| AI / NLP | RAG Pipeline, Text Embeddings, Vector Search, Conversational LLM |
| Bot Platform | Telegram Bot API |
| Voice | Speech-to-Text, Text-to-Speech |
| UI / UX | Telegram Inline Buttons, Conversational Flows |

---

## 🏗️ System Architecture
```
Telegram User
      ↓
Telegram Bot UI
      ↓
FastAPI Backend
      ↓
ML Models + RAG Engine
      ↓
PostgreSQL (Neon)
      ↓
Response to User
```

---

## 🚀 Deployment Status

- ✅ Backend ready
- ✅ ML models trained
- ✅ RAG implemented
- ✅ Database connected
- ✅ Telegram bot integrated

Coming Soon:
- 🌐 Public Telegram bot launch
- ☁️ Production cloud hosting
- 🏛️ Government schemes integration
- 🌾 Farmer datasets
- 📊 Analytics dashboard

---

## 🚀 Getting Started — Clone and Run Locally

### 📋 Prerequisites

Before running the bot, make sure you have:

- 🐍 Python 3.9 or higher installed
- 📦 pip package manager
- 🐘 PostgreSQL or a Neon Cloud account
- 💬 A Telegram Bot Token from @BotFather
- 🔑 An API key for your LLM (OpenAI, Groq, or any compatible provider)

---

### 📥 Step 1 — Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/grahmin-sahayak-bot.git
cd grahmin-sahayak-bot
```

---

### 🐍 Step 2 — Create a Virtual Environment
```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

---

### 📦 Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 🔐 Step 4 — Set Up Environment Variables

Create a .env file in the root directory:
```bash
cp .env.example .env
```

Fill in your credentials inside .env:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=your_postgresql_or_neon_db_url_here
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=your_embedding_model_name
```

---

### 🗄️ Step 5 — Set Up the Database
```bash
python setup_db.py
```

💡 If using Neon Cloud, just paste your connection string in DATABASE_URL — no local Postgres needed!

---

### 🧠 Step 6 — Build the RAG Knowledge Base

Place your knowledge base files (PDFs, TXTs) inside the /docs folder, then run:
```bash
python ingest.py
```

---

### 🤖 Step 7 — Train or Load ML Models
```bash
python train_model.py
```

✅ Pre-trained models will be saved in the /models directory. Skip this step if models are already present.

---

### ▶️ Step 8 — Run the FastAPI Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

🌐 Backend will be live at: http://localhost:8000

---

### 💬 Step 9 — Start the Telegram Bot

Open a new terminal, keep the backend running, and run:
```bash
python bot.py
```

🎉 Your bot is now live! Open Telegram, search your bot, and send /start

---

## 📁 Project Structure
```
grahmin-sahayak-bot/
│
├── app/                  # FastAPI backend
│   ├── main.py
│   ├── routes/
│   └── models/
│
├── bot.py                # Telegram bot entry point
├── ingest.py             # RAG document ingestion
├── train_model.py        # ML model training
├── setup_db.py           # Database setup
│
├── models/               # Trained ML models
├── docs/                 # Knowledge base documents
├── vector_store/         # Embedded vector data
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 Quick Test Checklist

- [ ] Bot responds to /start
- [ ] Loan eligibility form works
- [ ] EMI calculation returns result
- [ ] RAG answers a question correctly
- [ ] Voice input/output works
- [ ] Language switching works

---

## 🐛 Common Issues and Fixes

| Issue | Fix |
|-------|-----|
| ModuleNotFoundError | Run pip install -r requirements.txt again |
| Bot not responding | Check TELEGRAM_BOT_TOKEN in .env |
| DB connection error | Verify DATABASE_URL is correct |
| RAG giving wrong answers | Re-run python ingest.py |
| Port already in use | Change port in uvicorn command |

---

## 🎯 Project Goal

To empower rural communities with:

- 📖 Financial literacy
- 🤖 AI-driven assistance
- 📱 Easy digital access
- 🛡️ Fraud protection
- 🌐 Multilingual support

All through one simple chatbot.

---

## 📌 Future Enhancements

- 🪪 Aadhaar-based verification
- 🏦 Real bank API integration
- 🌾 Crop advisory system
- 🌦️ Weather alerts
- 📋 Scheme auto-matching
- 📱 Mobile app version

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

1. 🍴 Fork the repo
2. 🌿 Create a new branch: git checkout -b feature/your-feature
3. 💾 Commit your changes: git commit -m "Add your feature"
4. 📤 Push to branch: git push origin feature/your-feature
5. 🔁 Open a Pull Request

---

## 👩‍💻 Built With

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

<div align="center">

### ❤️ Vision

"Technology should reach villages before it reaches luxury."

Grahmin Sahayak Bot is a step toward inclusive AI for rural India.

⭐ Star this repo if you believe in tech for rural empowerment!

</div>
