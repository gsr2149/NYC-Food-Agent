import uuid

from dotenv import load_dotenv

load_dotenv()  # load .env before agent reads env vars

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from app import run_turn  

app = FastAPI(title="NYC Food Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        reply, tool_calls = run_turn(session_id, req.message)
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            raise HTTPException(
                status_code=429,
                detail="I've reached my daily limit for recommendations. Please try again later.",
            )
        raise HTTPException(status_code=500, detail=str(e))
    return {"response": reply, "session_id": session_id, "tool_calls": tool_calls}
