from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float

    def timestamp(self) -> str:
        def fmt(s):
            return f"{int(s // 60)}:{int(s % 60):02d}"
        return f"{fmt(self.start)} – {fmt(self.end)}"


@dataclass
class SearchHit:
    segment: TranscriptSegment
    score: float  # L2 distance — lower is better


@dataclass
class QueryResult:
    query: str
    detected_language: str
    answer: str
    answer_en: str
    hits: list[SearchHit] = field(default_factory=list)
    evaluation: dict = field(default_factory=dict)
