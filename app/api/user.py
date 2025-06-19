from fastapi import APIRouter, Request, Response
from app.services.session_service import SessionService
import uuid
router = APIRouter(prefix="/user")
session_service = SessionService()

@router.get("/history")
async def get_history(request: Request):
    session_id = session_service.get_or_create_session_id(request)
    return session_service.get_history(session_id)

@router.get("/session")
async def get_session(request: Request, response: Response):
    ## 세션 쿠키 발급 및 반환
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"session_id": session_id}