from fastapi import APIRouter, Depends, HTTPException, status


from sqlalchemy.orm import Session
from db.session import get_db


from models.user import User, UserRole
from schemas.user import UserCreate, UserRead, UserUpdate


from core.security import hash_password, verify_password

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