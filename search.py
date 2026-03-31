from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from storage.session_store import SessionStore
from services.response_generator import answer_query, evaluate_answer

router = APIRouter(tags=["search"])


class QueryRequest(BaseModel):
    session_id: str
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=10)
    evaluate: bool = False


class SegmentOut(BaseModel):
    text: str
    timestamp: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    answer_en: str
    detected_language: str
    segments: list[SegmentOut]
    evaluation: dict


@router.post("/query", response_model=QueryResponse)
async def query_video(req: QueryRequest):
    index = SessionStore.get(req.session_id)
    if index is None:
        raise HTTPException(404, "Session not found. Please upload and process a video first.")

    hits = index.search(req.question, k=req.top_k)
    if not hits:
        raise HTTPException(422, "No relevant segments found for that query.")

    result = answer_query(req.question, hits)

    evaluation = {}
    if req.evaluate:
        evaluation = evaluate_answer(result)

    return QueryResponse(
        answer=result.answer,
        answer_en=result.answer_en,
        detected_language=result.detected_language,
        segments=[
            SegmentOut(
                text=h.segment.text,
                timestamp=h.segment.timestamp(),
                score=round(h.score, 4),
            )
            for h in result.hits
        ],
        evaluation=evaluation,
    )
