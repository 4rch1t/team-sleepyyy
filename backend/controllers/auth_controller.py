import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import get_db
from models.user import User
from auth import get_password_hash, create_access_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=201)
def register(request: AuthRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if user:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        hashed_pw = get_password_hash(request.password)
        new_user = User(email=request.email, hashed_password=hashed_pw)
        db.add(new_user)
        db.commit()
        return {"detail": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during user registration")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login", status_code=200)
def login(request: AuthRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during user login")
        raise HTTPException(status_code=500, detail="Internal server error")
