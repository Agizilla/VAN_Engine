import sys
import socket
import uvicorn
import subprocess
from pathlib import Path
from contextlib import closing, asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
LEXICON_PATH = BASE_DIR / "lexicon.json"

def kill_port(port: int = 7860):
    """Kill process on port to avoid conflicts"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/f', '/pid', pid], capture_output=True)
                        print(f"[*] Killed process {pid} on port {port}")
                    except:
                        pass
    except:
        pass

for port in range(7860, 7871):
    kill_port(port)

sys.path.insert(0, str(BASE_DIR))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] House Codex API ready at http://localhost:7860")
    yield
    print("[*] Shutting down...")

app = FastAPI(title="House Codex API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app_gradio import generate_verse as _generate_verse, load_lexicon, get_lexicon_stats, GLUE_WORDS

class VerseRequest(BaseModel):
    archetype: str = "Chaos"
    bar_count: int = 8
    spb: float = 16.0
    use_glue: bool = True

class Settings(BaseModel):
    archetype: str = "Chaos"
    bar_count: int = 8
    spb: float = 16.0
    use_glue: bool = True

settings = Settings()

@app.get("/")
async def root():
    return {"status": "online", "service": "House Codex Lyrical Engine"}

@app.get("/stats")
async def stats():
    return {"stats": get_lexicon_stats()}

@app.post("/generate")
async def generate(req: VerseRequest):
    try:
        verse = _generate_verse(
            req.archetype,
            req.bar_count,
            req.spb,
            req.use_glue
        )
        return {"verse": verse, "settings": req.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    return settings.dict()

@app.post("/settings")
async def save_settings(s: Settings):
    global settings
    settings = s
    return {"status": "saved", "settings": settings.dict()}

import re

def strip_markdown_for_clipboard(text: str) -> str:
    """Strip Markdown formatting for clean clipboard output"""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\|', '', text)
    text = re.sub(r'[-:]+\s*', '', text)
    text = re.sub(r'```', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

@app.get("/clipboard")
async def get_clipboard_format(verse: str):
    return {"text": strip_markdown_for_clipboard(verse)}

@app.get("/glue-words")
async def get_glue():
    return GLUE_WORDS

def find_free_port(start=7860, end=7900):
    for port in range(start, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start

if __name__ == "__main__":
    port = 7860
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    
    print(f"[*] Starting House Codex API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")