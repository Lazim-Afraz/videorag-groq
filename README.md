# VideoRAG (Groq edition)

A production-grade Video Question-Answering system.  
Upload a video → transcribed with Whisper → indexed with FAISS → queryable via Groq LLM.

## File structure

```
server.py                  ← FastAPI app, lifespan, CORS, static mount
video.py                   ← POST /api/upload
search.py                  ← POST /api/query
model_registry.py          ← singleton for Whisper + LaBSE
audio_transcription.py     ← Whisper transcription
embedding_index.py         ← FAISS index build + search
response_generator.py      ← Groq answer + LLM-judge eval
transcript.py              ← TranscriptSegment, SearchHit, QueryResult
session_store.py           ← in-memory session → index map
upload_cache.py            ← temp file save / delete
requirements.txt
.env.example
index.html / styles.css / app.js  ← frontend (served by FastAPI)
```

---

## Run locally

### 1. Prerequisites

- Python 3.10+
- ffmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)
- A [Groq API key](https://console.groq.com/)

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY
```

### 4. Start the server

```bash
uvicorn server:app --reload
# Open http://localhost:8000
```

---

## Deploy to Railway (recommended)

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select your repo
4. In **Variables**, add:
   - `GROQ_API_KEY` = your key
   - `GROQ_MODEL` = `llama-3.1-8b-instant` (or any Groq model)
   - `WHISPER_MODEL` = `base`
5. Railway auto-detects `nixpacks.toml` and installs ffmpeg + Python deps
6. Your app is live at the Railway URL 🎉

## Deploy to Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your repo
4. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `GROQ_API_KEY`, `GROQ_MODEL`, `WHISPER_MODEL`
6. Add a **build command pre-step** for ffmpeg: use Docker deploy instead (see below)

## Deploy with Docker (Fly.io, Render, any VPS)

```bash
docker build -t videorag .
docker run -p 8000:8000 -e GROQ_API_KEY=your_key videorag
```

For Fly.io:
```bash
fly launch   # follow prompts
fly secrets set GROQ_API_KEY=your_key
fly deploy
```

---

## Available Groq models

| Model | Speed | Quality |
|-------|-------|---------|
| `llama-3.1-8b-instant` | Fastest | Good |
| `llama-3.3-70b-versatile` | Fast | Best |
| `mixtral-8x7b-32768` | Fast | Good, long context |
| `gemma2-9b-it` | Fast | Good |
