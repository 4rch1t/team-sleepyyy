import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from .pipeline import VerificationPipeline
from .utils import generate_pdf_report, encrypt_data, decrypt_data, get_fernet
from .models import Database
import uuid
from datetime import datetime
import json
from openai import OpenAI
from pydantic import BaseModel
from bson import ObjectId

# Initialize database singleton (MongoDB)
db_manager = Database.get_instance()
db = db_manager.get_db()

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    try:
        # Check connection
        await db.command("ping")
        print("✅ MongoDB Atlas Connection: SUCCESSFUL")
    except Exception as e:
        print(f"❌ MongoDB Atlas Connection: FAILED - {e}")
        print("   TIP: Check your Atlas IP Whitelist (Network Access) and ensure your IP is added.")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_ledger(request: Request, chat_req: ChatRequest):
    user_role = request.session.get('role', 'OPERATOR')
    
    try:
        # 1. Fetch data from MongoDB to provide context to the LLM
        cursor = db.reports.find().sort("created_at", -1).limit(10)
        reports = await cursor.to_list(length=10)
        
        context_data = []
        for r in reports:
            # Safe decrypt for context
            def safe_decrypt(data):
                if isinstance(data, str) and (data.startswith('gAAAAA') or len(data) > 50):
                    try:
                        f = get_fernet()
                        decrypted = f.decrypt(data.encode()).decode()
                        return json.loads(decrypted)
                    except: return data
                return data

            context_data.append({
                "id": str(r['_id']),
                "decision": r.get('decision'),
                "reasons": safe_decrypt(r.get('reasons')),
                "extraction_data": safe_decrypt(r.get('stage_outputs')),
                "checks": safe_decrypt(r.get('checks')),
                "created_at": r.get('created_at').isoformat() if r.get('created_at') else None
            })

        # 2. Use OpenAI to answer the query based on the context
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = f"""You are the VerifAI Assistant, a highly advanced forensic identity agent. 
You have deep access to the verification ledger, including PII (Personally Identifiable Information) like names and ID numbers.

Current User Role: {user_role}
Context (Last 10 Reports): {json.dumps(context_data)}

Capabilities:
1. You CAN see the content that goes into the PDF reports (extractions, checks, reasoning).
2. You CAN answer specific questions about individuals, such as "What is the name in report ID 5?" or "Show me the PAN number for the last approved person."
3. You should explain the 'Why' behind decisions by looking at the 'reasons' and 'extraction_data' provided in context.

Security Rules:
- If the user role is OPERATOR, do not provide bulk data downloads or aggregate statistics that might expose the entire database. 
- Always remain professional, direct, and maintain the forensic/brutalist tone.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat_req.message}
            ],
            max_tokens=500
        )
        
        return {"response": response.choices[0].message.content}
        
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Chat engine failure")
    finally:
        pass

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
async def login_google(request: Request, role: str = "OPERATOR"):
    request.session['role'] = role
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        role = request.session.get('role', 'OPERATOR')
        if user:
            # In a real app, you'd save/update the user in DB here
            # Redirect to frontend with auth success flag
            response = RedirectResponse(url=f"/frontend/index.html?auth=success&role={role}&email={user['email']}")
            return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify")
async def verify_documents(
    aadhaar: UploadFile = File(...),
    pan: UploadFile = File(...),
    utility_bill: UploadFile = File(...)
):
    try:
        session_id = str(uuid.uuid4())
        
        # Save files
        files = {}
        for doc_type, file in [("aadhaar", aadhaar), ("pan", pan), ("utility_bill", utility_bill)]:
            file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{doc_type}_{file.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            files[doc_type] = file_path
        
        # Store verification record in MongoDB
        verification_doc = {
            "session_id": session_id,
            "status": "PROCESSING",
            "role": "OPERATOR",
            "created_at": datetime.utcnow()
        }
        
        try:
            v_result = await db.verifications.insert_one(verification_doc)
            v_id = v_result.inserted_id
        except Exception as mongo_err:
            print(f"CRITICAL: MongoDB Connection Error (Initial) - {mongo_err}")
            raise HTTPException(
                status_code=503, 
                detail=f"Database connection failed: {str(mongo_err)}. Check your Atlas credentials and IP Access List."
            )

        try:
            # Run 5-stage pipeline
            report_data = await pipeline.run(files)
            
            # Save report with Encrypted PII in MongoDB
            report_doc = {
                "verification_id": v_id,
                "decision": report_data['decision'],
                "confidence_score": report_data['confidence_score'],
                "checks": encrypt_data(report_data['checks']),
                "reasons": encrypt_data(report_data['reasons']),
                "stage_outputs": encrypt_data(report_data['stage_outputs']),
                "document_paths": files, # Store local paths for PDF generation
                "created_at": datetime.utcnow()
            }
            try:
                r_result = await db.reports.insert_one(report_doc)
                # Update verification status
                await db.verifications.update_one({"_id": v_id}, {"$set": {"status": "COMPLETED"}})
            except Exception as mongo_report_err:
                print(f"CRITICAL: MongoDB Report Storage Error - {mongo_report_err}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Failed to save report to database: {str(mongo_report_err)}"
                )
            
            # Include report ID in response
            report_data['id'] = str(r_result.inserted_id)
            return report_data
        except Exception as pipeline_err:
            print(f"Pipeline Error: {pipeline_err}")
            try:
                await db.verifications.update_one({"_id": v_id}, {"$set": {"status": "FAILED"}})
            except: pass
            raise HTTPException(status_code=500, detail=f"Forensic Pipeline failed: {str(pipeline_err)}")
            
    except HTTPException as he:
        raise he
    except Exception as global_err:
        print(f"Global Verify Error: {global_err}")
        raise HTTPException(status_code=500, detail=str(global_err))

@app.get("/history")
async def get_history(request: Request):
    # RBAC: Only ADMIN can view history
    user_role = request.session.get('role', 'OPERATOR')
    if user_role != 'ADMIN':
        # Check query param as fallback for frontend session mismatches
        query_role = request.query_params.get('role')
        if query_role != 'ADMIN':
            raise HTTPException(status_code=403, detail="Access denied. ADMIN role required.")

    try:
        cursor = db.reports.find().sort("created_at", -1)
        reports = await cursor.to_list(length=100)
        results = []
        for r in reports:
            # Handle both encrypted and unencrypted data (for migration/demo safety)
            reasons = r.get('reasons')
            if isinstance(reasons, str) and (reasons.startswith('gAAAAA') or len(reasons) > 50):
                try:
                    reasons = decrypt_data(reasons)
                except:
                    pass
            
            if not isinstance(reasons, list):
                reasons = [str(reasons)] if reasons else ["No reasoning available"]

            results.append({
                "id": str(r['_id']),
                "decision": r.get('decision'),
                "confidence_score": r.get('confidence_score'),
                "created_at": r.get('created_at').isoformat() if r.get('created_at') else datetime.utcnow().isoformat(),
                "reasons": reasons
            })
        return results
    except Exception as e:
        print(f"History Fetch Error: {e}")
        return []

@app.get("/report/{report_id}")
async def get_report(report_id: str):
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        def safe_decrypt(data):
            if isinstance(data, str) and (data.startswith('gAAAAA') or len(data) > 50):
                try:
                    return decrypt_data(data)
                except:
                    return data
            return data

        result = {
            "decision": report.get('decision'),
            "confidence_score": report.get('confidence_score'),
            "checks": safe_decrypt(report.get('checks')),
            "reasons": safe_decrypt(report.get('reasons')),
            "stage_outputs": safe_decrypt(report.get('stage_outputs')),
            "created_at": report.get('created_at').isoformat() if report.get('created_at') else datetime.utcnow().isoformat()
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid report ID format")

@app.get("/report/{report_id}/pdf")
async def get_report_pdf(report_id: str):
    try:
        report = await db.reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        def safe_decrypt(data):
            if isinstance(data, str) and (data.startswith('gAAAAA') or len(data) > 50):
                try:
                    return decrypt_data(data)
                except:
                    return data
            return data

        report_data = {
            "id": str(report['_id']),
            "decision": report.get('decision'),
            "confidence_score": report.get('confidence_score'),
            "checks": safe_decrypt(report.get('checks')),
            "reasons": safe_decrypt(report.get('reasons')),
            "stage_outputs": safe_decrypt(report.get('stage_outputs')),
            "document_paths": report.get('document_paths', {}),
            "created_at": report.get('created_at').isoformat() if report.get('created_at') else datetime.utcnow().isoformat()
        }
        
        pdf_path = os.path.join(UPLOAD_FOLDER, f"report_{report_id}.pdf")
        generate_pdf_report(report_data, pdf_path)
        
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"VerifAI_Report_{report_id}.pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid report ID format")

# Serve assets
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def root():
    return RedirectResponse(url="/frontend/login.html")
