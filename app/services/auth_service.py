from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.security import hash_password, verify_password

def register_user(name:str, email: str, password: str, db: Session):
    if db.query(User).filter(User.email == email).first():
        return None
    try:
        hashed = hash_password(password)
        user = User(name = name, email = email, hashed_password = hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
    except:
        raise Exception()
    return user

def authenticate_user(email: str, password: str, db:Session):
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, str(user.hashed_password)):
        return user
    return None
