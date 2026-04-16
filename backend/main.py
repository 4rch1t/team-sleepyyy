import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from .pipeline import VerificationPipeline
from .models import Base, Verification, Report
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

# Initialize database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./verifai.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# OAuth Setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER_PATH", "./uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

pipeline = VerificationPipeline()

# Auth Routes
@app.get("/auth/login")
async def login_google(request: Request):
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        if user:
            # In a real app, you'd save/update the user in DB here
            # For this demo, we'll redirect back to frontend with a success flag
            response = RedirectResponse(url="/frontend/index.html")
            # We use a simple cookie or localStorage strategy for the demo
            # Here we just redirect; the frontend script will handle the 'logged in' state
            return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify")
async def verify_documents(
    aadhaar: UploadFile = File(...),
    pan: UploadFile = File(...),
    utility_bill: UploadFile = File(...)
):
    session_id = str(uuid.uuid4())
    
    # Save files
    files = {}
    for doc_type, file in [("aadhaar", aadhaar), ("pan", pan), ("utility_bill", utility_bill)]:
        file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{doc_type}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        files[doc_type] = file_path
    
    # Store verification record
    db = SessionLocal()
    verification = Verification(session_id=session_id, status="PROCESSING")
    db.add(verification)
    db.commit()
    
    try:
        # Run 5-stage pipeline
        report_data = await pipeline.run(files)
        
        # Save report
        report = Report(
            verification_id=verification.id,
            decision=report_data['decision'],
            confidence_score=report_data['confidence_score'],
            checks=report_data['checks'],
            reasons=report_data['reasons'],
            stage_outputs=report_data['stage_outputs']
        )
        db.add(report)
        verification.status = "COMPLETED"
        db.commit()
        
        return report_data
    except Exception as e:
        verification.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/history")
async def get_history():
    db = SessionLocal()
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    results = []
    for r in reports:
        results.append({
            "id": r.id,
            "decision": r.decision,
            "confidence_score": r.confidence_score,
            "created_at": r.created_at.isoformat(),
            "reasons": r.reasons
        })
    db.close()
    return results

@app.get("/report/{report_id}")
async def get_report(report_id: int):
    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        db.close()
        raise HTTPException(status_code=404, detail="Report not found")
    
    result = {
        "decision": report.decision,
        "confidence_score": report.confidence_score,
        "checks": report.checks,
        "reasons": report.reasons,
        "stage_outputs": report.stage_outputs,
        "created_at": report.created_at.isoformat()
    }
    db.close()
    return result

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/frontend/login.html")
