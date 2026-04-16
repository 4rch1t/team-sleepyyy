from sqlalchemy import Column, Integer, String, JSON, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Verification(Base):
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, index=True)
    decision = Column(String) # APPROVED, ESCALATED, REJECTED
    confidence_score = Column(Float)
    checks = Column(JSON)
    reasons = Column(JSON)
    stage_outputs = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
