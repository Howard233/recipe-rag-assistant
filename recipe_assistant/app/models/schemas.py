# app/models/schemas.py
from pydantic import BaseModel
from typing import Optional


class QuestionRequest(BaseModel):
    question: str
    llm_model: Optional[str] = None
    limit: Optional[int] = 5


class QuestionResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    feedback: int


class FeedbackResponse(BaseModel):
    conversation_id: str
    feedback: int
