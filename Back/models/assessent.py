import uuid
import enum
from sqlalchemy import Column, Enum, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base


class QuestionType(enum.Enum):  # PascalCase for classes
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    short_answer = "short_answer"


class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)  # ← added default
    name = Column(String, nullable=False)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pupil_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    evaluator = relationship("User", foreign_keys=[evaluator_id], back_populates="test_as_evaluator")
    pupil = relationship("User", foreign_keys=[pupil_id], back_populates="test_as_pupil")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")  # ← cascade


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)  # ← added default
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)  # ← fixed class name
    question_text = Column(String, nullable=False)
    question_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    test = relationship("Test", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")  # ← cascade


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)  # ← added default
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_number = Column(Integer, nullable=False)
    answer_text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    question = relationship("Question", back_populates="answers")