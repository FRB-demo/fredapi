"""API router for the chat / natural language interface."""

from fastapi import APIRouter

from app.models import ChatRequest
from app.services.chat_service import process_chat_message

router = APIRouter()


@router.post("/")
async def chat(request: ChatRequest):
    """Process a natural language query about economic data."""
    result = process_chat_message(request.message, request.context)
    return result
