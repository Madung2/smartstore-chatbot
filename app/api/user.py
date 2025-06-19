from fastapi import APIRouter, Request, Response
from app.services.session_service import SessionService

router = APIRouter(prefix="/user")
session_service = SessionService()

@router.get("/history")
async def get_history(request: Request):
    session_id = session_service.get_or_create_session_id(request)
    return session_service.get_history(session_id)