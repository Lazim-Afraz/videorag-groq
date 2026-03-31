from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.audio_transcription import transcribe
from services.embedding_index import EmbeddingIndex
from storage.upload_cache import save_upload, remove
from storage.session_store import SessionStore

router = APIRouter(tags=["video"])


class ProcessResponse(BaseModel):
    session_id: str
    segment_count: int
    message: str


@router.post("/upload", response_model=ProcessResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """
    Accept a video file, transcribe it with Whisper, build a FAISS index,
    and return a session_id the client uses for subsequent queries.
    """
    content = await file.read()
    if not content:
        raise HTTPException(400, "Uploaded file is empty.")

    try:
        video_path = save_upload(content, file.filename or "upload.mp4")
    except ValueError as exc:
        raise HTTPException(415, str(exc))

    try:
        segments = transcribe(str(video_path))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Transcription failed: {exc}")
    finally:
        remove(video_path)

    index = EmbeddingIndex(segments)
    session_id = SessionStore.create(index)

    return ProcessResponse(
        session_id=session_id,
        segment_count=len(segments),
        message=f"Indexed {len(segments)} transcript segments.",
    )
