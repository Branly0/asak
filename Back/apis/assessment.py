from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from db.session import get_db
from core.security import get_current_user
from models.user import User, UserRole
from models.assessent import Test, Question, Answer, Result, StudentAnswer, QuestionType
from schemas.assessment import (
    TestCreate, TestRead, TestUpdate, TestReadWithQuestions,
    QuestionCreate, QuestionRead, AnswerCreate, AnswerRead,
    TestSubmission, StudentAnswerSubmit, ResultRead, TestResultsDashboard,
    TestResultSummary, PDFExtractedQuestion
)
from utils.pdf_extraction import extract_questions_from_pdf
from uuid import UUID
from typing import List

router = APIRouter(
    prefix="/tests",
    tags=["assessment"],
)


def _require_evaluator(current_user: User = Depends(get_current_user)):
    """Verify user is a teacher (evaluator)"""
    if current_user.role != UserRole.evaluator:
        raise HTTPException(status_code=403, detail="Only teachers can perform this action")
    return current_user


def _require_pupil(current_user: User = Depends(get_current_user)):
    """Verify user is a student (pupil)"""
    if current_user.role != UserRole.pupil:
        raise HTTPException(status_code=403, detail="Only students can perform this action")
    return current_user


@router.post("/create", response_model=TestRead)
def create_test(
    test_data: TestCreate,
    current_user: User = Depends(_require_evaluator),
    db: Session = Depends(get_db)
):
    """Create a new test"""
    new_test = Test(
        name=test_data.name,
        description=test_data.description,
        evaluator_id=current_user.id,
        is_published=False
    )
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


@router.post("/{test_id}/questions", response_model=QuestionRead)
def add_question_to_test(
    test_id: UUID,
    question_data: QuestionCreate,
    current_user: User = Depends(_require_evaluator),
    db: Session = Depends(get_db)
):
    """Add questions to a test"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own tests")

    if test.is_published:
        raise HTTPException(status_code=400, detail="Cannot add questions to published tests")

    # Create question
    new_question = Question(
        test_id=test_id,
        question_type=question_data.question_type,
        question_text=question_data.question_text,
        question_number=question_data.question_number
    )
    db.add(new_question)
    db.flush()

    # Create answers
    for idx, answer_data in enumerate(question_data.answers, 1):
        new_answer = Answer(
            question_id=new_question.id,
            answer_number=idx,
            answer_text=answer_data.answer_text,
            is_correct=answer_data.is_correct
        )
        db.add(new_answer)

    db.commit()
    db.refresh(new_question)
    return new_question


@router.post("/{test_id}/upload-pdf")
async def upload_pdf_and_extract(
    test_id: UUID,
    file: UploadFile = File(...),
    past_exam: bool = False,
    current_user: User = Depends(_require_evaluator),
    db: Session = Depends(get_db)
):
    """Upload PDF and extract questions using OpenAI"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own tests")

    if test.is_published:
        raise HTTPException(status_code=400, detail="Cannot add questions to published tests")

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Extract questions using OpenAI
    try:
        extracted_questions = extract_questions_from_pdf(content, past_exam=past_exam)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract from PDF: {str(e)}")

    # Save extracted questions
    saved_questions = []
    for idx, q_data in enumerate(extracted_questions, 1):
        new_question = Question(
            test_id=test_id,
            question_type=QuestionType.multiple_choice,
            question_text=q_data.get("question_text", ""),
            question_number=idx
        )
        db.add(new_question)
        db.flush()

        for answer_idx, answer_data in enumerate(q_data.get("answers", []), 1):
            new_answer = Answer(
                question_id=new_question.id,
                answer_number=answer_idx,
                answer_text=answer_data.get("answer_text", ""),
                is_correct=answer_data.get("is_correct", False)
            )
            db.add(new_answer)

        db.flush()
        saved_questions.append(new_question)

    db.commit()

    return {
        "message": f"Extracted {len(saved_questions)} questions from PDF",
        "test_id": str(test_id),
        "questions_count": len(saved_questions)
    }


async def _read_file(file: UploadFile) -> bytes:
    """Helper to read file content"""
    return await file.read()


@router.patch("/{test_id}/publish", response_model=TestRead)
def publish_test(
    test_id: UUID,
    current_user: User = Depends(_require_evaluator),
    db: Session = Depends(get_db)
):
    """Publish a test (make it available for students)"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only publish your own tests")

    # Verify test has questions
    questions_count = db.query(Question).filter(Question.test_id == test_id).count()
    if questions_count == 0:
        raise HTTPException(status_code=400, detail="Cannot publish test with no questions")

    test.is_published = True
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/{test_id}/results", response_model=TestResultsDashboard)
def get_test_results(
    test_id: UUID,
    current_user: User = Depends(_require_evaluator),
    db: Session = Depends(get_db)
):
    """Get results dashboard for a test (teacher view)"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view results for your own tests")

    results = db.query(Result).filter(Result.test_id == test_id).all()

    results_summary = []
    for result in results:
        results_summary.append(
            TestResultSummary(
                student_id=result.pupil_id,
                student_name=result.pupil.name,
                student_email=result.pupil.email,
                score=result.score,
                total_questions=result.total_questions,
                submitted_at=result.submitted_at
            )
        )

    return TestResultsDashboard(
        test_id=test_id,
        test_name=test.name,
        results=results_summary
    )


@router.get("/available", response_model=List[TestRead])
def get_available_tests(
    current_user: User = Depends(_require_pupil),
    db: Session = Depends(get_db)
):
    """Get list of published tests available for students"""
    tests = db.query(Test).filter(Test.is_published == True).all()
    return tests


@router.get("/{test_id}/questions", response_model=TestReadWithQuestions)
def get_test_questions(
    test_id: UUID,
    current_user: User = Depends(_require_pupil),
    db: Session = Depends(get_db)
):
    """Get test questions (without revealing correct answers)"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if not test.is_published:
        raise HTTPException(status_code=403, detail="This test is not published yet")

    questions = db.query(Question).filter(Question.test_id == test_id).all()

    # Hide is_correct from answers
    test_data = TestReadWithQuestions(
        id=test.id,
        name=test.name,
        description=test.description,
        is_published=test.is_published,
        evaluator_id=test.evaluator_id,
        created_at=test.created_at,
        updated_at=test.updated_at,
        questions=[]
    )

    for question in questions:
        answers = db.query(Answer).filter(Answer.question_id == question.id).all()
        question_data = QuestionRead(
            id=question.id,
            question_text=question.question_text,
            question_type=question.question_type,
            question_number=question.question_number,
            answers=[
                AnswerRead(
                    id=answer.id,
                    answer_number=answer.answer_number,
                    answer_text=answer.answer_text,
                    is_correct=False  # Hide correct answer
                )
                for answer in answers
            ]
        )
        test_data.questions.append(question_data)

    return test_data


@router.post("/{test_id}/submit", response_model=ResultRead)
def submit_test(
    test_id: UUID,
    submission: TestSubmission,
    current_user: User = Depends(_require_pupil),
    db: Session = Depends(get_db)
):
    """Submit test answers and get results"""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if not test.is_published:
        raise HTTPException(status_code=403, detail="This test is not published")

    questions = db.query(Question).filter(Question.test_id == test_id).all()
    total_questions = len(questions)

    if total_questions == 0:
        raise HTTPException(status_code=400, detail="Test has no questions")

    # Create result record
    result = Result(
        test_id=test_id,
        pupil_id=current_user.id,
        score=0,
        total_questions=total_questions
    )
    db.add(result)
    db.flush()

    # Process each answer
    correct_count = 0
    for submission_answer in submission.answers:
        question = db.query(Question).filter(Question.id == submission_answer.question_id).first()
        if not question:
            continue

        is_correct = False

        if question.question_type == QuestionType.short_answer:
            # For short answer, check exact match
            correct_answer = db.query(Answer).filter(
                and_(Answer.question_id == question.id, Answer.is_correct == True)
            ).first()
            if correct_answer and submission_answer.answer_text:
                is_correct = submission_answer.answer_text.strip().lower() == correct_answer.answer_text.strip().lower()

            student_answer = StudentAnswer(
                result_id=result.id,
                question_id=question.id,
                answer_text=submission_answer.answer_text,
                is_correct=is_correct
            )
        else:
            # For multiple choice / true false
            if submission_answer.selected_answer_id:
                selected_answer = db.query(Answer).filter(
                    Answer.id == submission_answer.selected_answer_id
                ).first()
                if selected_answer:
                    is_correct = selected_answer.is_correct

            student_answer = StudentAnswer(
                result_id=result.id,
                question_id=question.id,
                selected_answer_id=submission_answer.selected_answer_id,
                is_correct=is_correct
            )

        if is_correct:
            correct_count += 1

        db.add(student_answer)

    # Calculate score (percentage)
    result.score = int((correct_count / total_questions) * 100)
    db.commit()
    db.refresh(result)

    return result


@router.get("/results/{result_id}", response_model=ResultRead)
def get_result_detail(
    result_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed result with all answers and corrections"""
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Check authorization
    if current_user.role == UserRole.pupil and result.pupil_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own results")
    if current_user.role == UserRole.evaluator and result.test.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view results from your own tests")

    # Get all student answers with correct answers
    student_answers = db.query(StudentAnswer).filter(StudentAnswer.result_id == result_id).all()

    result_data = ResultRead(
        id=result.id,
        test_id=result.test_id,
        pupil_id=result.pupil_id,
        score=result.score,
        total_questions=result.total_questions,
        submitted_at=result.submitted_at,
        student_answers=[]
    )

    for student_answer in student_answers:
        question = db.query(Question).filter(Question.id == student_answer.question_id).first()

        # Get correct answer for this question
        correct_answer = db.query(Answer).filter(
            and_(Answer.question_id == student_answer.question_id, Answer.is_correct == True)
        ).first()

        answer_read = {
            "id": student_answer.id,
            "question_id": student_answer.question_id,
            "selected_answer_id": student_answer.selected_answer_id,
            "answer_text": student_answer.answer_text,
            "is_correct": student_answer.is_correct,
            "question_text": question.question_text if question else None,
            "correct_answer_id": correct_answer.id if correct_answer else None,
            "correct_answer_text": correct_answer.answer_text if correct_answer else None
        }
        result_data.student_answers.append(answer_read)

    return result_data
