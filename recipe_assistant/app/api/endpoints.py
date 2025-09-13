from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    QuestionRequest,
    QuestionResponse,
    FeedbackRequest,
    FeedbackResponse,
)
import uuid
from datetime import datetime

from ...rag import rag
from ...db import save_conversation, save_feedback

router = APIRouter()


@router.post("/question", response_model=QuestionResponse)
async def handle_question(request: QuestionRequest):
    """answer user's query

    Args:
        request (QuestionRequest): user's query
    """

    try:
        conversation_id = str(uuid.uuid4())
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if request.llm_model:
            answer = rag(request.question, request.llm_model, request.limit)
        else:
            answer = rag(request.question, limit=request.limit)

        response = QuestionResponse(
            conversation_id=conversation_id, question=request.question, answer=answer['answer']
        )

        # save convsersation
        save_conversation(conversation_id=conversation_id,
                          question=request.question,
                          answer_data=answer
                          )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def handle_feedback(request: FeedbackRequest):
    """acknowledge users' feedbacks

    Args:
        request (FeedbackRequest): user's feedback
    """
    try:
        conversation_id = request.conversation_id
        feedback = request.feedback

        if not request.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required")

        save_feedback(
            conversation_id=conversation_id,
            feedback=feedback,
        )

        # Create response
        response = FeedbackResponse(
            conversation_id=conversation_id,
            feedback=feedback,
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing feedback: {str(e)}"
        )
