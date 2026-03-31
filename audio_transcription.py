import librosa
import numpy as np

from domain.transcript import TranscriptSegment
from services.model_registry import ModelRegistry


def transcribe(video_path: str) -> list[TranscriptSegment]:
    """
    Load audio from the video file and run Whisper on it.
    Returns one TranscriptSegment per Whisper segment.
    """
    audio, _ = librosa.load(video_path, sr=16000, mono=True)
    result = ModelRegistry.get().whisper.transcribe(audio)

    segments = [
        TranscriptSegment(
            text=seg["text"].strip(),
            start=seg["start"],
            end=seg["end"],
        )
        for seg in result["segments"]
        if seg["text"].strip()
    ]

    if not segments:
        raise ValueError("Whisper returned no speech segments for this file.")

    return segments
