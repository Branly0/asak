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

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=True)
    is_published = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    evaluator = relationship("User", foreign_keys=[evaluator_id], back_populates="test_as_evaluator")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="test", cascade="all, delete-orphan")


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

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    answer_number = Column(Integer, nullable=False)
    answer_text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    question = relationship("Question", back_populates="answers")


class Result(Base):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False)
    pupil_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    test = relationship("Test", back_populates="results")
    pupil = relationship("User", back_populates="results")
    student_answers = relationship("StudentAnswer", back_populates="result", cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey("results.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    selected_answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=True)
    answer_text = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    result = relationship("Result", back_populates="student_answers")
    question = relationship("Question")
    selected_answer = relationship("Answer")