from fastapi import FastAPI
from app.api.devops import router as devops_router


app = FastAPI(
    title="Smartstore FAQ Chatbot API",
    description="Smartstore FAQ 데이터셋 전처리 및 챗봇 API",
    version="1.0.0"
)

app.include_router(devops_router)

@app.get("/")
def read_root():
    return {"message": "Smartstore FAQ Chatbot API is running."}