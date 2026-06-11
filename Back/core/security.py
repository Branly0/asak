## hasshing and verifying the password 
from passlib.context import CryptContext

def hash_password(password: str) -> str:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.verify(password, hashed_password)


########################## JWT token generation and verification utilities using PyJWT
from fastapi import HTTPException

from jose import jwt
from datetime import datetime, timedelta
from core.setting import settings
from models.token import Token
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.user import User

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS  

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"type": "access", "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"type": "refresh", "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def refresh_access_token(refresh_token: str) -> str:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        email: str = payload.get("sub")
        #check if the refresh token is active
        db = SessionLocal()
        token = db.query(Token).filter(Token.token == refresh_token).first()
        if not token.is_active:
            raise ValueError("Token has been revoked, you are logged out")
        if email is None:
            token.is_active = False
            db.add(token)
            db.commit()
            raise ValueError("Invalid token")
        return create_access_token(data={"sub": email})
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.JWTError:
        raise ValueError("Invalid token")



## Authentication function to verify user credentials
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def authenticate_user(email: str, password: str):
    """Authenticate user by email and password."""
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    db.close()

    if not user or not verify_password(password, user.hs_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current user from the access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user