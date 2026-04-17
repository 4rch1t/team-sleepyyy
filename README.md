
CREDITS FINISHED SO NO DEMO VIDEO, ONLY SCREENSHOTS, PPT AND FLOW CHART IS BELOW DEMO SCREENSHOTS

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/c65bca46-6f57-4181-b6fb-d6b0d8a79cac" />
<img width="1915" height="910" alt="image" src="https://github.com/user-attachments/assets/42885ecc-b7f9-47d4-946d-00c4cb70d720" />
<img width="1911" height="917" alt="image" src="https://github.com/user-attachments/assets/cbd0adaa-5220-4ebd-bdae-3d03a48c463c" />
<img width="1919" height="923" alt="image" src="https://github.com/user-attachments/assets/c9011d03-d2a3-4747-8c54-3677c51c3bb5" />
<img width="1902" height="916" alt="image" src="https://github.com/user-attachments/assets/db0d0255-e22d-4b9f-8bb9-083b7aac66c1" />
<img width="657" height="863" alt="image" src="https://github.com/user-attachments/assets/d9b16f6a-4df9-4ddd-ae27-085d8119a416" />
<img width="662" height="867" alt="image" src="https://github.com/user-attachments/assets/5da01cbb-579f-443d-bb12-0816e99a9c03" />
<img width="430" height="537" alt="image" src="https://github.com/user-attachments/assets/21bd4933-7daf-402a-b4d5-8bfe0213cd7b" />


FLOW CHART 

<img width="1536" height="1024" alt="project flowcharts" src="https://github.com/user-attachments/assets/a22ad90d-0614-4a1e-ac62-154dced8175a" />




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
