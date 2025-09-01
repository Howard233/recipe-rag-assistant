# app/models/schemas.py
from pydantic import BaseModel
from typing import Any, Dict, Optional

class QuestionRequest(BaseModel):
    question: str
    # context: Optional[str] = None
    # user_id: Optional[str] = None

class QuestionResponse(BaseModel):
    conversation_id: str
    question: str
    answer: str

class FeedbackRequest(BaseModel):
    conversation_id: str
    feedback: str

class FeedbackResponse(BaseModel):
    conversation_id: str
    feedback: str