from sqlalchemy import Column, Integer, String, JSON, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Database:
    _instance = None
    _engine = None
    _SessionLocal = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    def __init__(self):
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./verifai.db")
        self._engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def create_all(self):
        Base.metadata.create_all(bind=self._engine)

    def get_session(self):
        return self._SessionLocal()

class Verification(Base):
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    role = Column(String, default="OPERATOR") # ADMIN, OPERATOR
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, index=True)
    decision = Column(String) # APPROVED, ESCALATED, REJECTED
    confidence_score = Column(Float)
    # Encrypted fields stored as strings
    checks = Column(String) 
    reasons = Column(String)
    stage_outputs = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
