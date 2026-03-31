import json
import os

from groq import Groq
from langdetect import detect, LangDetectException

from domain.transcript import SearchHit, QueryResult


def _get_client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _chat(client: Groq, prompt: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def _context_block(hits: list[SearchHit]) -> str:
    return "\n".join(h.segment.text for h in hits)


def answer_query(query: str, hits: list[SearchHit]) -> QueryResult:
    client = _get_client()
    context = _context_block(hits)

    try:
        lang = detect(query)
    except LangDetectException:
        lang = "en"

    native_answer = _chat(
        client,
        f"You are a multilingual video assistant.\n"
        f'The user asked (in {lang}): "{query}"\n\n'
        f"Relevant transcript excerpts:\n---\n{context}\n---\n\n"
        f"Answer clearly and concisely in the same language as the question.",
    )

    english_answer = _chat(
        client,
        f'The user asked: "{query}"\n\n'
        f"Relevant transcript excerpts:\n---\n{context}\n---\n\n"
        f"Give a concise English answer grounded in the transcript above.",
    )

    return QueryResult(
        query=query,
        detected_language=lang,
        answer=native_answer,
        answer_en=english_answer,
        hits=hits,
    )


def evaluate_answer(result: QueryResult) -> dict:
    client = _get_client()
    context = _context_block(result.hits)

    raw = _chat(
        client,
        f"You are an impartial evaluator.\n\n"
        f"USER QUERY: {result.query}\n\n"
        f"RETRIEVED CONTEXT:\n{context}\n\n"
        f"GENERATED ANSWER:\n{result.answer_en}\n\n"
        f"Score 0-10 on: Relevance, Accuracy, Fluency, Overall.\n"
        f'Return only valid JSON: {{"Relevance":0,"Accuracy":0,"Fluency":0,"Overall":0,"Comments":""}}',
    )

    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"Comments": raw}
