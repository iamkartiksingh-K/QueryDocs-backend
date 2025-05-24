from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserOut, Token
from app.services.auth_service import register_user, authenticate_user
from app.utils.security import create_access_token

router = APIRouter()

@router.post("/register", response_model=Token)
def register (user: UserCreate, db: Session = Depends(get_db)):
    new_user = register_user(user.email, user.password, db)
    if not new_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
