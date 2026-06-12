import gradio as gr
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent
LEXICON_PATH = BASE_DIR / "lexicon.json"

SYLLABLE_CORRECTIONS = {
    "battle": 2, "metal": 2, "temple": 2, "ample": 2,
    "subtle": 2, "title": 2, "gentle": 2, "juggle": 2,
    "wrestle": 2, "struggle": 2, "topple": 2, "ripple": 2,
    "babble": 2, "gabble": 2, "nibble": 2, "dribble": 2,
    "bubble": 2, "double": 2, "trouble": 2, "cube": 2,
    "cave": 2, "love": 1, "move": 1, "prove": 1,
    "whose": 1, "lose": 1, "choose": 1, "chaos": 2,
    "anarchy": 3, "axiom": 3, "medium": 3, "catastrophe": 4,
    "hierarchy": 4, "architecture": 5, "aberration": 4,
}

GLUE_WORDS = [
    {"token": "the", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "and", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "in", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "of", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "to", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "a", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "my", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "on", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "for", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
    {"token": "is", "syllables": 1, "archetype": "glue", "energy_score": 0.0},
]

def load_lexicon():
    if LEXICON_PATH.exists():
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            words = data.get("lexicon", [])
            
            for w in words:
                token = w.get("token", "").lower()
                if token in SYLLABLE_CORRECTIONS:
                    w["syllables"] = SYLLABLE_CORRECTIONS[token]
            
            data["lexicon"] = words
            return data
    return {"lexicon": [], "glue_words": GLUE_WORDS}

def generate_verse(archetype, bar_count=8, spb=14.0, use_glue=True):
    data = load_lexicon()
    words = data.get("lexicon", [])
    glue = GLUE_WORDS if use_glue else []
    
    if not words:
        return "Error: lexicon.json not found. Run digest_lexicons.py first."
    
    verse_lines = []
    half = bar_count // 2
    
    archetype_map = {
        "Chaos": ("Chaos", "Codex"),
        "Codex": ("Codex", "Chaos"),
        "Gatswaai": ("Gatswaai", "Gatswaai"),
        "Gatvuller": ("Chaos", "Chaos"),
        "Gatstamper": ("Codex", "Codex"),
        "Butler": ("Codex", "Chaos"),
    }
    
    primary, secondary = archetype_map.get(archetype, ("Chaos", "Codex"))
    
    for i in range(bar_count):
        phase = "Gatvuller" if i < half else "Gatstamper"
        current_archetype = primary if i < half else secondary
        
        candidates = [w for w in words if w.get("archetype") == current_archetype]
        
        if not candidates:
            verse_lines.append(f"| {i+1:02} | [LOW] | [no tokens] |")
            continue
        
        total_syllables = 0
        selected = []
        
        while total_syllables < spb and candidates:
            if use_glue and glue and total_syllables < spb - 1 and random.random() > 0.3:
                g = random.choice(glue)
                selected.append(g)
                total_syllables += g["syllables"]
            
            word = random.choice(candidates)
            syllables = word.get("syllables", 1)
            
            if total_syllables + syllables <= spb:
                selected.append(word)
                total_syllables += syllables
                candidates.remove(word)
            
            if total_syllables >= spb:
                break
        
        if selected:
            raw_tokens = [w["token"].lower() for w in selected]
            formatted_bar = " ".join(raw_tokens).capitalize()
            if not formatted_bar.endswith(('.', '!', '?')):
                formatted_bar += "."
            
            energy = sum(w.get("energy_score", 0) for w in selected) / len(selected)
            energy_label = "[HIGH]" if energy >= 0.6 else "[MED]" if energy >= 0.3 else "[LOW]"
            verse_lines.append(f"| {i+1:02} | {energy_label} | {formatted_bar} |")
        else:
            verse_lines.append(f"| {i+1:02} | [LOW] | [fill] |")
    
    header = f"## 🎤 Generated Verse: {archetype}\n"
    header += f"> **Density**: {spb} SPB | **Bars**: {bar_count}\n\n"
    header += f"| # | Energy | Lyrical Content |\n|:---|:---:|:---|\n"
    
    result = header + "\n".join(verse_lines)
    result += f"\n\n---\n**Metadata**: {json.dumps({'bars': bar_count, 'spb': spb, 'archetype': archetype, 'phases': {'Gatvuller': f'1-{half}', 'Gatstamper': f'{half+1}-{bar_count}'}, 'glue_words': use_glue}, indent=2)}"
    
    return result

def get_lexicon_stats():
    data = load_lexicon()
    words = data.get("lexicon", [])
    
    by_archetype = {}
    for w in words:
        a = w.get("archetype", "Unknown")
        by_archetype[a] = by_archetype.get(a, 0) + 1
    
    stats = f"**Total tokens**: {len(words)}\n\n"
    stats += "**By archetype:**\n"
    for a, c in sorted(by_archetype.items()):
        stats += f"- {a}: {c}\n"
    stats += f"\n**Glue words**: {len(GLUE_WORDS)}"
    
    return stats

def build_app():
    with gr.Blocks(title="House Codex - Lyrical Engine") as app:
        gr.Markdown("""
        # 🎙️ House Codex - Lyrical Engine
        
        Sovereign chopper/slap-clap verse generator using phonetic lexicon.
        
        **Gat Lifecycle:**
        - **Gatvuller** (Bars 1-4): Chaos archetype - problem/hole
        - **Gatstamper** (Bars 5-8): Codex archetype - solution/build
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                archetype = gr.Dropdown(
                    ["Chaos", "Codex", "Gatswaai", "Gatvuller", "Gatstamper", "Butler"],
                    value="Chaos",
                    label="Archetype"
                )
                bar_count = gr.Number(value=8, precision=0, minimum=4, maximum=16, label="Number of Bars")
                spb = gr.Slider(minimum=8, maximum=24, step=1, value=14, label="Syllables Per Bar")
                use_glue = gr.Checkbox(value=True, label="Include Glue Words")
                
                generate_btn = gr.Button("Generate Verse", variant="primary")
            
            with gr.Column(scale=1):
                stats_btn = gr.Button("Refresh Stats")
                stats_output = gr.Textbox(label="Lexicon Stats", lines=8)
        
        output = gr.Markdown(label="Generated Verse")
        
        generate_btn.click(
            fn=generate_verse,
            inputs=[archetype, bar_count, spb, use_glue],
            outputs=output
        )
        
        stats_btn.click(
            fn=get_lexicon_stats,
            inputs=[],
            outputs=stats_output
        )
        
        gr.Markdown("""
        ### Fields
        
        - **Archetype**: Mood/theme
        - **Bars**: Number of bars (4-16)
        - **Syllables/Bar**: SPB density (10-18)
        - **Glue Words**: Add "the", "and", "in", etc.
        
        ### Energy Scoring
        
        - High (≥0.6): Hard plosives + fricatives
        - Medium (0.3-0.6): Balanced
        - Low (<0.3): Vowel-heavy
        """)
    
    return app

if __name__ == "__main__":
    import sys
    import socket
    
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        arch = sys.argv[2] if len(sys.argv) > 2 else 'Chaos'
        bars = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        spb = float(sys.argv[4]) if len(sys.argv) > 4 else 16.0
        print(generate_verse(arch, bars, spb, use_glue=True))
        sys.exit(0)
    
    def find_free_port(start=7860, end=7900):
        for port in range(start, end + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return start
    
    port = find_free_port()
    print(f"[*] Starting Gradio UI on port {port}...")
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=port)