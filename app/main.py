from fastapi import FastAPI
from app.api.devops import router as devops_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.user import router as user_router

app = FastAPI(
    title="Smartstore FAQ Chatbot API",
    description="Smartstore FAQ 데이터셋 전처리 및 챗봇 API",
    version="1.0.0"
)

app.include_router(devops_router)
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(user_router)

@app.get("/")
def read_root():
    return {"message": "Smartstore FAQ Chatbot API is running."}