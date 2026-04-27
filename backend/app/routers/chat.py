"""API router for the chat / natural language interface."""

import logging

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest
from app.services.chat_service import process_chat_message

logger = logging.getLogger("econsight.chat")

router = APIRouter()


@router.post("/")
async def chat(request: ChatRequest):
    """Process a natural language query about economic data."""
    try:
        context = [item.model_dump() for item in request.context] if request.context else None
        result = process_chat_message(request.message, context)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Chat processing failed")
        raise HTTPException(status_code=500, detail="Failed to process chat message")
