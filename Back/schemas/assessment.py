from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import enum


class QuestionTypeEnum(str, enum.Enum):
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    short_answer = "short_answer"


class AnswerCreate(BaseModel):
    answer_text: str
    is_correct: bool


class AnswerRead(BaseModel):
    id: UUID
    answer_number: int
    answer_text: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionTypeEnum
    question_number: int
    answers: List[AnswerCreate]


class QuestionRead(BaseModel):
    id: UUID
    question_text: str
    question_type: QuestionTypeEnum
    question_number: int
    answers: List[AnswerRead]

    class Config:
        from_attributes = True


class QuestionReadWithoutAnswers(BaseModel):
    id: UUID
    question_text: str
    question_type: QuestionTypeEnum
    question_number: int

    class Config:
        from_attributes = True


class TestCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TestRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_published: bool
    evaluator_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestReadWithQuestions(TestRead):
    questions: List[QuestionRead] = []


class StudentAnswerSubmit(BaseModel):
    question_id: UUID
    selected_answer_id: Optional[UUID] = None
    answer_text: Optional[str] = None


class TestSubmission(BaseModel):
    answers: List[StudentAnswerSubmit]


class StudentAnswerRead(BaseModel):
    id: UUID
    question_id: UUID
    selected_answer_id: Optional[UUID]
    answer_text: Optional[str]
    is_correct: bool
    question_text: Optional[str] = None
    correct_answer_id: Optional[UUID] = None
    correct_answer_text: Optional[str] = None

    class Config:
        from_attributes = True


class ResultRead(BaseModel):
    id: UUID
    test_id: UUID
    pupil_id: UUID
    score: int
    total_questions: int
    submitted_at: datetime
    student_answers: List[StudentAnswerRead] = []

    class Config:
        from_attributes = True


class ResultWithTestInfo(ResultRead):
    test_name: Optional[str] = None
    test_description: Optional[str] = None


class TestResultSummary(BaseModel):
    student_id: UUID
    student_name: str
    student_email: str
    score: int
    total_questions: int
    submitted_at: datetime


class TestResultsDashboard(BaseModel):
    test_id: UUID
    test_name: str
    results: List[TestResultSummary] = []


class PDFExtractedQuestion(BaseModel):
    question_text: str
    answers: List[dict]
