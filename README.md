<img width="921" height="731" alt="image" src="https://github.com/user-attachments/assets/31ddd741-9712-4fd3-9719-a737abbe1042" />

# VerifAI — AI-Powered KYC + AML Document Verification for India

VerifAI is an automated system designed to streamline the KYC (Know Your Customer) process for Indian financial institutions. It processes **Aadhaar**, **PAN**, and **Utility Bills** through a specialized 5-stage reasoning pipeline to provide explainable decisions.

## 🚀 Core Features

- **Brutalist UI**: A high-contrast, sharp, and modern interface built for efficiency.
- **5-Stage Pipeline**:
  1. **Tamper Detection**: Uses Error Level Analysis (ELA) to detect image forensics anomalies.
  2. **Structured Extraction**: Leverages OpenAI Vision API for precise field-level data extraction.
  3. **Cross-Document Consistency**: Uses `RapidFuzz` for fuzzy name matching across documents.
  4. **Compliance Rule Engine**: Validates PAN/Aadhaar formats and checks for PEP (Politically Exposed Persons).
  5. **Confidence Scoring**: Weighted scoring system (APPROVED / ESCALATED / REJECTED).
- **Explainable Reports**: Transparent reasoning for every verification decision.
- **Local-First**: Runs entirely locally without Docker, using SQLite and local storage.

## 🛠️ Tech Stack

- **Backend**: Python 3.14+, FastAPI, SQLAlchemy, OpenAI API
- **Frontend**: Brutalist HTML/CSS (Pure CSS + Vanilla JS)
- **Database**: SQLite (Local)
- **Libraries**: Pillow, NumPy, RapidFuzz, PyYAML, Cryptography

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory (refer to `.env.example`):
```env
OPENAI_API_KEY=your_key_here
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_fernet_key
DATABASE_URL=sqlite:///./verifai.db
PEP_DATA_PATH=./pep_data.json
UPLOAD_FOLDER_PATH=./uploads
```

### 3. Run the Application
Start the backend server:
```bash
python run.py
```
Then, open `frontend/index.html` in your web browser.

## ⚖️ Compliance Rules
Custom rules are managed in `backend/rules.yaml`:
- Utility bill must be ≤ 90 days old.
- Aadhaar must be exactly 12 digits.
- PAN must match the standard regex pattern.

## 📜 License
MIT
