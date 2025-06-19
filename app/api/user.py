from fastapi import APIRouter, Request, Response
from app.services.session_service import SessionService
import uuid
router = APIRouter(prefix="/user")
session_service = SessionService()

@router.get("/history")
async def get_history(request: Request):
    sessionid = session_service.get_or_create_sessionid(request)
    return session_service.get_history(sessionid)

@router.get("/session")
async def get_session(request: Request, response: Response):
    ## 세션 이 없다면 쿠키 발급 및 반환
    sessionid = request.cookies.get("sessionid")
    if not sessionid:
        sessionid = str(uuid.uuid4())
        response.set_cookie(key="sessionid", value=sessionid, httponly=True)
        return {"sessionid": sessionid, "type": "new"}
    return {"sessionid": sessionid, "type": "stored"}


@router.get("/new_session")
async def new_session(request: Request, response: Response):
    # 세션 쿠키 발급 및 반환
    sessionid = str(uuid.uuid4())
    response.set_cookie(key="sessionid", value=sessionid, httponly=True)
    return {"sessionid": sessionid, "type": "new"}