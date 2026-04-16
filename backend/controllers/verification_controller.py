import logging
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from db import get_db
from config import settings
from auth import get_current_user
from models.user import User
from models.verification import Verification

from services.tamper_detection import check_tampering
from services.extraction import extract_document_data
from services.consistency import check_consistency
from services.compliance import check_compliance
from services.scoring import calculate_score

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verify", tags=["verify"])

@router.post("", status_code=201)
async def verify_documents(
    aadhaar: UploadFile = File(...),
    pan: UploadFile = File(...),
    utility_bill: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate file types and size
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        files = [aadhaar, pan, utility_bill]
        for f in files:
            if f.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail=f"Invalid file type for {f.filename}. Must be jpeg, png, or pdf.")
            
        a_bytes = await aadhaar.read()
        p_bytes = await pan.read()
        u_bytes = await utility_bill.read()
        
        # Checking size limit roughly 5MB each (5 * 1024 * 1024 = 5242880)
        for name, b in zip(["aadhaar", "pan", "utility_bill"], [a_bytes, p_bytes, u_bytes]):
            if len(b) > 5242880:
                raise HTTPException(status_code=400, detail=f"File {name} exceeds 5MB limit.")
        
        # Stage 1: Tamper Detection (Assess all)
        a_tamper = check_tampering(a_bytes)
        p_tamper = check_tampering(p_bytes)
        u_tamper = check_tampering(u_bytes)
        
        tamper_result = a_tamper
        if p_tamper.is_tampered: tamper_result = p_tamper
        if u_tamper.is_tampered: tamper_result = u_tamper
        
        if not tamper_result.is_tampered:
            a_ext = extract_document_data(a_bytes, "AADHAAR")
            p_ext = extract_document_data(p_bytes, "PAN")
            u_ext = extract_document_data(u_bytes, "UTILITY_BILL")
            
            consistency = check_consistency(a_ext, p_ext, u_ext)
            compliance = check_compliance(a_ext, p_ext, u_ext)
            
            score_data = calculate_score(tamper_result, a_ext, p_ext, u_ext, consistency, compliance)
        else:
            # Construct a hardfail result for tamper rejection
            breakdown = {
                "tamper": {"score": 0.0, "weight": 0.30, "details": tamper_result.reason},
                "extraction": {"score": 0.0, "weight": 0.20, "low_confidence_fields": []},
                "consistency": {"score": 0.0, "weight": 0.25, "mismatches": []},
                "compliance": {"score": 0.0, "weight": 0.25, "rules": []}
            }
            # Ad-hoc structure mimicking ScoreResult
            class ScoreStub:
                def __init__(self):
                    self.decision = 'REJECTED'
                    self.score = 0.0
                    self.breakdown = breakdown
            score_data = ScoreStub()

        report_json_str = json.dumps({
            "decision": score_data.decision,
            "confidence_score": score_data.score,
            "breakdown": score_data.breakdown
        })
        
        # Save to DB with pgcrypto encryption
        # Using cast to bytea allows encrypt/decrypt via postgres symmetric keys safely.
        query = text("""
            INSERT INTO verifications (user_id, decision, confidence_score, report_json, created_at)
            VALUES (:uid, :dec, :score, encode(pgp_sym_encrypt(:rjson, :ekey), 'base64'), now())
            RETURNING id, created_at
        """)
        
        result = db.execute(query, {
            "uid": current_user.id,
            "dec": score_data.decision,
            "score": score_data.score,
            "rjson": report_json_str,
            "ekey": settings.ENCRYPTION_KEY
        })
        inserted = result.fetchone()
        db.commit()
        
        return {"detail": "Verification processed", "id": inserted.id, "decision": score_data.decision}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing verification")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history", status_code=200)
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        verifications = db.query(Verification.id, Verification.created_at, Verification.decision, Verification.confidence_score).filter(Verification.user_id == current_user.id).order_by(Verification.created_at.desc()).all()
        return [
            {
                "id": str(v.id),
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "decision": v.decision,
                "confidence_score": v.confidence_score
            }
            for v in verifications
        ]
    except Exception as e:
        logger.exception("Error fetching history")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{verification_id}", status_code=200)
def get_verification(verification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        query = text("""
            SELECT id, user_id, decision, confidence_score, created_at, 
                   pgp_sym_decrypt(decode(report_json, 'base64'), :ekey) as rep_json 
            FROM verifications 
            WHERE id = :vid AND user_id = :uid
        """)
        
        result = db.execute(query, {
            "vid": verification_id,
            "uid": current_user.id,
            "ekey": settings.ENCRYPTION_KEY
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Verification not found")
            
        return {
            "id": str(result.id),
            "decision": result.decision,
            "confidence_score": result.confidence_score,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "report": json.loads(result.rep_json)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching verification {verification_id}")
        raise HTTPException(status_code=500, detail="Internal server error")
