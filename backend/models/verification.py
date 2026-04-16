import uuid
import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db import Base

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False) # APPROVED | ESCALATED | REJECTED
    confidence_score = Column(Float, nullable=False)
    
    # Store directly as string/text (ciphertext). 
    # The encrypt/decrypt logic with pgcrypto will be managed at the query level.
    report_json = Column(String, nullable=False) 
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User")
