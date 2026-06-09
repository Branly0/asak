from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from uuid import UUID

class UserRole(str, Enum):
    evaluator = "evaluator"
    pupil = "pupil"

class UserSex(str, Enum):
    male = "male"
    female = "female"

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    name: str
    age: int
    sex: UserSex
    password: str
    role: UserRole

class UserRead(UserBase):
    id: UUID
    name: str
    age: int

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[UserSex] = None
