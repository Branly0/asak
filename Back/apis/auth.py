from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm


from sqlalchemy.orm import Session
from db.session import get_db


from models.user import User, UserRole
from schemas.user import UserCreate, UserRead, UserUpdate, UserLogin
from models.token import Token


from core.security import authenticate_user, authenticate_user, create_access_token, create_refresh_token, hash_password, refresh_access_token, get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create new user
    new_user = User(
        name=user.name,
        age=user.age,
        sex=user.sex,
        email=user.email,
        hs_password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Verify user credentials
    authenticated_user = authenticate_user(form_data.username, form_data.password)
    if not authenticated_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": authenticated_user.email})
    refresh_token = create_refresh_token(data={"sub": authenticated_user.email})
    # Store refresh token in the database
    db_token = Token(
        token=refresh_token,
        user_id=authenticated_user.id,
        is_active=True
        )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"} 
  
@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        new_access_token = refresh_access_token(refresh_token)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    

@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Revoke all active tokens for the user
    tokens = db.query(Token).filter(Token.user_id == current_user.id, Token.is_active == True).all()
    for token in tokens:
        token.is_active = False
        db.add(token)
    db.commit()
    return {"message": "Successfully logged out"}