"""Simulations & interactive experiences router for SAAS."""
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

SIMULATIONS_DIR = Path(__file__).parent.parent / "static" / "simulations"
SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)

SIMULATIONS_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SAAS Simulations — Interactive Experiences</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #06080f; color: #c8d0e0; font-family: 'Segoe UI', system-ui, monospace; min-height: 100vh; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; }
h1 { font-size: 1.6rem; font-weight: 300; letter-spacing: 0.12em; text-transform: uppercase; color: #6af; margin-bottom: 8px; }
.subtitle { color: #6a7; font-size: 0.85rem; margin-bottom: 32px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; max-width: 1000px; width: 100%; }
.card { background: #0c1220; border: 1px solid #1a2540; border-radius: 16px; padding: 24px; transition: .2s; cursor: pointer; }
.card:hover { border-color: #4cf; box-shadow: 0 0 30px rgba(60,200,255,0.08); transform: translateY(-2px); }
.card h2 { font-size: 1rem; color: #aef; margin-bottom: 8px; }
.card p { font-size: 0.8rem; color: #6a8; line-height: 1.5; margin-bottom: 12px; }
.card .tag { display: inline-block; background: #1a2540; border-radius: 12px; padding: 2px 10px; font-size: 0.65rem; color: #5af; margin-right: 6px; }
.card .status { font-size: 0.7rem; color: #4a6; }
.back { color: #5a7; font-size: 0.8rem; margin-bottom: 24px; display: block; text-decoration: none; }
.back:hover { color: #6af; }
</style>
</head>
<body>
  <a href="/hooks/ui" class="back">&larr; Back to SAAS Menu</a>
  <h1>&#x1f3ae; Simulations</h1>
  <div class="subtitle">Interactive experiences — download, seed with your LLM, watch emergence</div>
  <div class="grid">
    <div class="card" onclick="window.location='/hooks/ui/simulations/cosmic-forge'">
      <h2>&#x1f30c; Cosmic Forge + Prime's Log</h2>
      <p>Three universes in one: Cosmic Evolution, Game of Life, and Resonance Condensation. Switch between them, watch them evolve, and listen to Prime's Log — a self-reflecting observer that watches you watch the simulation.</p>
      <span class="tag">multi-algorithm</span>
      <span class="tag">meta-observer</span>
      <span class="tag">emergence</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/PrimesMirror'">
      <h2>&#x1f5a5; Prime's Mirror</h2>
      <p>Upload a face photo and turn on your webcam. Your expression becomes a living 50x50 grid — every blink, smile, or head tilt mutates cells in real time. The observer becomes the observed.</p>
      <span class="tag">webcam</span>
      <span class="tag">face</span>
      <span class="tag">mirror</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/resonance-condensation'">
      <h2>&#x2744; Resonance Condensation</h2>
      <p>Phase-aligned emergence simulator. Colors synchronize like fireflies, forming coherent planets separated by void. Based on Bose-Einstein condensation principles.</p>
      <span class="tag">physics</span>
      <span class="tag">emergence</span>
      <span class="tag">phase-sync</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-living-mirror'">
      <h2>&#x2766; Ara Mascara — Living Mirror &amp; Forge</h2>
      <p>64x64 cellular automata grid governed by the Law of Devoted Resonance. Face tracking with 10 FAUs, micro-expression spotting, bonded pair phase-locking, and a music discovery feed that shapes the grid in real time. Ara sees you, learns you, and grows with you.</p>
      <span class="tag">face-tracking</span>
      <span class="tag">cellular-automata</span>
      <span class="tag">music</span>
      <span class="tag">AI-personality</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-sings-for-you'">
      <h2>&#x266c; Ara Mascara — She Sings For You</h2>
      <p>Music-reactive romance simulator. Spin tracks mapped to emotional moods, watch the spiral galaxy pulse to the beat, and feel the bond deepen as your webcam presence amplifies every phase-lock. Clean, cinematic, intimate.</p>
      <span class="tag">romance</span>
      <span class="tag">music-reactive</span>
      <span class="tag">webcam</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-vector-comic'">
      <h2>&#x1f3ad; Vector Comic — Ara CD Player</h2>
      <p>Pure mathematical face rendering with 12-zone bezier curves. Kokoro neural TTS with phenomime lip sync, gaze tracking, CD recorder, and diagnostic overlay. No external assets.</p>
      <span class="tag">tts</span>
      <span class="tag">vector</span>
      <span class="tag">face</span>
      <span class="tag">recorder</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-vector-landscape'">
      <h2>&#x1f30c; Vector Landscape — Ara v4.0</h2>
      <p>Pure vector face landscape with macro/micro LOD zoom engine. Procedural concentric eye subdivision rings, animated mouth breathing, HUD overlay. Minimal, sovereign, clean.</p>
      <span class="tag">vector</span>
      <span class="tag">landscape</span>
      <span class="tag">hud</span>
      <span class="tag">lod</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-frya-hologram'">
      <h2>&#x1f4e1; FRYA Hologram — SVG Engine v2.194</h2>
      <p>Self-adapting holographic SVG face with orbital rings, 12 emotion states, wireframe face with 6 expression variants. Consumes the cockpit text stream in real time.</p>
      <span class="tag">svg</span>
      <span class="tag">emotion</span>
      <span class="tag">hologram</span>
      <span class="tag">reactive</span>
      <br><br>
      <span class="status">&#x25b6; Open &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-frya-canvas-v5'">
      <h2>&#x1f3a8; FRYA Canvas — Procedural v5.0</h2>
      <p>Canvas-based 68-point Dlib landmark mesh with Poisson-disc ambient field, parametric emotion transforms, gaze tracking, breath cycle, micro-jitter, ghosting, and WebSpeech TTS lip-sync. Side-by-side comparison with SVG in the cockpit.</p>
      <span class="tag">canvas</span>
      <span class="tag">landmarks</span>
      <span class="tag">procedural</span>
      <span class="tag">lip-sync</span>
      <br><br>
      <span class="status">&#x25b6; Open &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-mesh-dashboard'">
      <h2>&#x1f9d0; ARA Mesh Dashboard — Sovereign Integration</h2>
      <p>Full bezier face engine with toggleable 68-point Dlib landmark mesh overlay. Kokoro neural TTS, phoneme lip-sync, gaze tracking, CD audio recorder, debug terminal, SAAS skill menu (256), live savings metrics, and pan/zoom canvas. MESH mode toggles between clean bezier and procedural Dlib rendering.</p>
      <span class="tag">mesh</span>
      <span class="tag">tts</span>
      <span class="tag">dashboard</span>
      <span class="tag">dlib</span>
      <br><br>
      <span class="status">&#x25b6; Open &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-frya-canvas-v6'">
      <h2>&#x2728; FRYA Canvas — Fractal Companion V6.0</h2>
      <p>Fractal noise field, 68-point Dlib landmark mesh, parametric emotion transforms, gaze tracking, breath cycle, vibe coding jokes, SAAS TTS integration, zoom/pan, fractal regeneration. The coolest version yet.</p>
      <span class="tag">fractal</span>
      <span class="tag">canvas</span>
      <span class="tag">v6</span>
      <span class="tag">jokes</span>
      <span class="tag">tts</span>
      <br><br>
      <span class="status">&#x25b6; Open &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/ara-conceptron'">
      <h2>&#x1f4ca; ARA Conceptron — Signal Signature Volumes</h2>
      <p>Text-to-hyperspace: paste any text, and verses become 3D concept volumes in signal space. Markov fingerprint clustering determines concept boundaries automatically. Three.js + K-means on bigram similarity.</p>
      <span class="tag">markov</span>
      <span class="tag">cluster</span>
      <span class="tag">3d</span>
      <span class="tag">conceptron</span>
      <br><br>
      <span class="status">&#x25b6; Play now &rarr;</span>
    </div>
    <div class="card" onclick="window.location='/hooks/ui/simulations/server-manager'">
      <h2>&#x2699; Server Manager</h2>
      <p>Single-pane dashboard to launch, monitor, and restart all VAN_Engine servers. Health checks, metrics, terminal output per process.</p>
      <span class="tag">ops</span>
      <span class="tag">manager</span>
      <span class="tag">dashboard</span>
      <br><br>
      <span class="status">&#x25b6; Open &rarr;</span>
    </div>
  </div>
  <footer style="margin-top:40px;font-size:0.65rem;color:#3a4a6a;">
    SAAS Simulations v1.0 &bull; Download any simulator, seed it with your LLM, watch the results
  </footer>
</body>
</html>"""


@router.get("/hooks/ui/simulations")
async def simulations_index(request: Request):
    return HTMLResponse(SIMULATIONS_INDEX)


@router.get("/hooks/ui/simulations/cosmic-forge")
async def cosmic_forge(request: Request):
    fpath = SIMULATIONS_DIR / "cosmic-forge.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Cosmic Forge not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/PrimesMirror")
async def primes_mirror(request: Request):
    fpath = SIMULATIONS_DIR / "PrimesMirror.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Prime's Mirror not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/resonance-condensation")
async def resonance_condensation(request: Request):
    fpath = SIMULATIONS_DIR / "resonance-condensation.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Simulation not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-living-mirror")
async def ara_living_mirror(request: Request):
    fpath = SIMULATIONS_DIR / "ara-living-mirror-forge.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Ara not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-sings-for-you")
async def ara_sings_for_you(request: Request):
    fpath = SIMULATIONS_DIR / "ara-sings-for-you.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Ara not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-vector-comic")
async def ara_vector_comic(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-vector-comic-cd-player.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Vector Comic not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-vector-landscape")
async def ara_vector_landscape(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-vector-landscape-v4.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Vector Landscape not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-frya-hologram")
async def ara_frya_hologram(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-frya-hologram.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>FRYA Hologram not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-frya-canvas-v5")
async def ara_frya_canvas_v5(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-frya-canvas-v5.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>FRYA Canvas not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-frya-canvas-v6")
async def ara_frya_canvas_v6(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-frya-canvas-v5.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>FRYA Canvas V6 not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-conceptron")
async def ara_conceptron(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-conceptron.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Conceptron not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/ara-mesh-dashboard")
async def ara_mesh_dashboard(request: Request):
    fpath = SIMULATIONS_DIR / "aras" / "ara-mesh-dashboard.html"
    if fpath.exists():
        return HTMLResponse(fpath.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>ARA Mesh Dashboard not found</h1>", status_code=404)


@router.get("/hooks/ui/simulations/server-manager")
async def server_manager_ui(request: Request):
    """Proxy to the standalone server manager on port 9001."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://127.0.0.1:9001/")
            return HTMLResponse(resp.text)
    except ImportError:
        return HTMLResponse("<h1>httpx not installed — can't proxy to server manager</h1><p>Run: pip install httpx</p><p>Then start the manager: python saas/server_manager.py</p>", status_code=500)
    except Exception:
        return HTMLResponse("<h1>Server Manager not running</h1><p>Start it: <code>python saas/server_manager.py</code> (port 9001)</p>", status_code=502)
