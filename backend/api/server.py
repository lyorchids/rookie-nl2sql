"""
FastAPI server for NL2SQL system with SSE streaming.
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import uuid
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from graphs.base_graph import stream_query

app = FastAPI(title="NL2SQL API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Stream NL2SQL query results via SSE.
    
    Events:
    - node_start: {"node": "parse_intent", "label": "解析意图"}
    - node_progress: {"node": "parse_intent", "label": "解析意图", "show": "..."}
    - token: {"content": "你"}
    - done: {}
    """
    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        async for event in stream_query(request.question, session_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
