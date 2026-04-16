# VerifAI - KYC Document Verification Application

## Problem Statement
KYC fraud and manual verification bottlenecks in Indian financial institutions cause significant delays and risk exposure.

## Solution
VerifAI provides a fast, automated, five-stage AI processing pipeline: 
1. **Tamper Detection** (Image Forensics & ELA)
2. **Extraction** (Structured Entity Extraction via OpenAI)
3. **Consistency** (Cross-referencing entities via Fuzzy String Matching)
4. **Compliance** (Regulatory rules & PEP Screening)
5. **Scoring** (Weighted outcome determination)

## Tech Stack
| Layer | Technology |
| --- | --- |
| Frontend | React (Vite), Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL (with `pgcrypto` for PII ciphertext) |
| AI Extraction | OpenAI API (GPT-4o) |
| Images & Logic | Pillow, NumPy, Rapidfuzz |
| Containerization | Docker, Docker Compose |

## How to Run
1. `cp .env.example .env` and fill the blank values.
2. Run `docker-compose up --build`.
3. Frontend: `http://localhost:5173`
4. Backend API docs: `http://localhost:8000/docs`

## Screenshots
[placeholder section]
