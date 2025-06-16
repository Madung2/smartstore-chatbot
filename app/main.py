from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Smartstore FAQ Chatbot API is running."} 