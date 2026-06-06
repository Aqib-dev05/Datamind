from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: int
    preview: List[Dict[str, Any]]
    column_info: List[Dict[str, Any]]


class QuestionOption(BaseModel):
    id: str
    label: str
    value: str


class Question(BaseModel):
    id: str
    question: str
    type: str  # "checkbox", "radio", "text"
    options: Optional[List[QuestionOption]] = None
    column: Optional[str] = None


class QuestionsResponse(BaseModel):
    file_id: str
    questions: List[Question]


class UserAnswers(BaseModel):
    file_id: str
    answers: Dict[str, Any]  # question_id -> selected value(s)
    output_format: str  # "csv" or "excel"


class ProcessResponse(BaseModel):
    success: bool
    message: str
    download_url: str
    summary: str
    stats: Dict[str, Any]
