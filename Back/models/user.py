from sqlalchemy import Column, Integer, Enum, String, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

import enum
import uuid

class UserRole(enum.Enum):
    evaluator = "evaluator"
    pupil = "pupil"

class UserSex(enum.Enum):
    male = "male"
    female = "female"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(Enum(UserSex), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hs_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ✅ Fix — lazy string evaluated later, after all models are loaded
    test_as_evaluator = relationship("Test", back_populates="evaluator", foreign_keys="Test.evaluator_id")
    test_as_pupil = relationship("Test", back_populates="pupil", foreign_keys="Test.pupil_id")