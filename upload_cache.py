import os
import tempfile
import uuid
from pathlib import Path

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", tempfile.gettempdir())) / "videorag_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def save_upload(content: bytes, original_filename: str) -> Path:
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    dest = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
    dest.write_bytes(content)
    return dest


def remove(path: Path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
