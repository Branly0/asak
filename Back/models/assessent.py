from sqlalchemy import Column, Enum, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.dialects.postgresql import UUID
from db.session import Base

class questionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, nullable=False)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pupil_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    evaluator = relationship("User", foreign_keys=[evaluator_id])
    pupil = relationship("User", foreign_keys=[pupil_id])

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    question_type = Column(Enum(questionType), nullable=False)
    question_text = Column(String, nullable=False)
    question_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    test = relationship("Test", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    question_type = Column(Enum(questionType), nullable=False)
    answer_number = Column(Integer, nullable=False)
    answer_text = Column(String, nullable=False)
    is_correct = Column(Integer, nullable=False)  # 1 for correct, 0 for incorrect
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    question = relationship("Question", back_populates="answers")