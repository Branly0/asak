import json
from typing import List, Dict
from google import genai
from core.setting import settings
import PyPDF2
from io import BytesIO


def _get_client():
    """Initialize Gemini client, raise error if API key not configured"""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured in environment")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def extract_questions_from_pdf(pdf_content: bytes, past_exam: bool = False) -> List[Dict]:
    """
    Extract questions and answers from PDF using Google Gemini.

    Args:
        pdf_content: Binary content of the PDF file
        past_exam: If True, treats it as a past exam and extracts existing Q&A
                   If False, generates Q&A from the text content

    Returns:
        List of dictionaries containing question_text and answers
    """

    # Extract text from PDF
    text_content = _extract_text_from_pdf(pdf_content)

    if not text_content.strip():
        raise ValueError("No text content extracted from PDF")

    # Prepare prompt based on document type
    if past_exam:
        prompt = f"""Extract all questions and answers from this past exam paper.
For each question, identify the correct answer(s).

Document content:
{text_content}

Return a JSON array with this structure:
[
  {{
    "question_text": "Question here",
    "answers": [
      {{"answer_text": "Option A", "is_correct": true}},
      {{"answer_text": "Option B", "is_correct": false}},
      {{"answer_text": "Option C", "is_correct": false}}
    ]
  }}
]

Return ONLY valid JSON, no markdown formatting."""
    else:
        prompt = f"""Generate practice questions and answers from this text content.
Create well-formed multiple choice questions with 3-4 options each.

Content:
{text_content}

Return a JSON array with this structure:
[
  {{
    "question_text": "Question here",
    "answers": [
      {{"answer_text": "Correct answer", "is_correct": true}},
      {{"answer_text": "Wrong answer", "is_correct": false}},
      {{"answer_text": "Wrong answer", "is_correct": false}}
    ]
  }}
]

Return ONLY valid JSON, no markdown formatting."""

    # Call Gemini API
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    response_text = response.text.strip()

    # Handle markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    questions_data = json.loads(response_text)

    return questions_data


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text content from PDF bytes."""
    try:
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"

        return text_content
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
