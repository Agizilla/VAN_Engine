import gradio as gr
import json
import random
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
LEXICON_PATH = BASE_DIR / "lexicon.json"

def load_lexicon():
    if LEXICON_PATH.exists():
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"lexicon": [], "glue_words": []}

def generate_verse(archetype, bar_count=8, spb=14.0):
    data = load_lexicon()
    words = data.get("lexicon", [])
    
    if not words:
        return "Error: lexicon.json not found. Run digest_lexicons.py first."
    
    verse_lines = []
    half = bar_count // 2
    
    for i in range(bar_count):
        phase = "Gatvuller" if i < half else "Gatstamper"
        current_archetype = "Chaos" if i < half else "Codex"
        
        candidates = [w for w in words 
                     if w.get("archetype") == current_archetype]
        
        if not candidates:
            verse_lines.append(f"Bar {i+1} ({phase}): [no tokens]")
            continue
        
        total_syllables = 0
        selected = []
        
        while total_syllables < spb and candidates:
            word = random.choice(candidates)
            syllables = word.get("syllables", 1)
            
            if total_syllables + syllables <= spb:
                selected.append(word)
                total_syllables += syllables
                candidates.remove(word)
            
            if total_syllables >= spb:
                break
        
        if selected:
            tokens = " ".join([w["token"] for w in selected])
            energy = sum(w.get("energy_score", 0) for w in selected) / len(selected)
            energy_label = "high" if energy >= 0.6 else "medium" if energy >= 0.3 else "low"
            verse_lines.append(f"Bar {i+1} ({phase}, {energy_label}): {tokens}")
        else:
            verse_lines.append(f"Bar {i+1} ({phase}): [fill]")
    
    meta = {
        "bars": bar_count,
        "spb": spb,
        "archetype": archetype,
        "phases": {"Gatvuller": "Bars 1-" + str(half), "Gatstamper": f"Bars {half+1}-{bar_count}"}
    }
    
    result = "### Generated Verse\n\n" + "\n".join(verse_lines)
    result += f"\n\n---\n**Metadata**: {meta}"
    
    return result

def create_lyrical_engine_tab():
    with gr.TabItem("Lyrical Engine"):
        gr.Markdown("""
        ### 🎙️ House Codex: Vocal Vessel Generator
        
        Generate chopper/slap-clap verses using the **Gat Lifecycle**:
        - **Gatvuller** (Bars 1-4): Chaos archetype - describes the problem/hole
        - **Gatstamper** (Bars 5-8): Codex archetype - the solution/build
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                archetype = gr.Dropdown(
                    choices=["Butler", "Gatstamper", "Gatvuller", "Codex", "Chaos"],
                    value="Gatstamper",
                    label="Lead Archetype",
                    info="Narrative voice for the verse"
                )
                
                bar_count = gr.Slider(
                    minimum=4, maximum=16, step=4, value=8,
                    label="Bar Count",
                    info="Typical verse = 8 bars"
                )
                
                spb = gr.Slider(
                    minimum=10, maximum=18, step=1, value=14,
                    label="Syllables Per Bar",
                    info="Chopper style = 14-16"
                )
                
                generate_btn = gr.Button(
                    "🎤 Forge Verse", 
                    variant="primary"
                )
            
            with gr.Column(scale=2):
                output = gr.Textbox(
                    label="Generated Lyrics",
                    lines=14,
                    show_copy_button=True
                )
                
                with gr.Row():
                    gr.Button("📋 Copy Text").click(
                        lambda x: x,
                        inputs=[output],
                        outputs=None
                    )
        
        generate_btn.click(
            fn=generate_verse,
            inputs=[archetype, bar_count, spb],
            outputs=output
        )
        
        gr.Markdown("""
        ---
        ### 📖 How It Works
        
        | Phase | Bars | Archetype | Theme |
        |-------|-----|-----------|-------|
        | Gatvuller | 1-4 | Chaos | Problem/Hole |
        | Gatstamper | 5-8 | Codex | Build/Solution |
        
        The generator pulls tokens from the digested lexicon based on:
        1. **Archetype match** (Chaos vs Codex)
        2. **Syllable fit** (matches SPB target)
        3. **Energy score** (high=hard, low=soft)
        """)

def build_demo():
    gr.Markdown("# House Codex - Lyrical Engine Demo")
    create_lyrical_engine_tab()

if __name__ == "__main__":
    demo = gr.Interface(
        fn=generate_verse,
        inputs=[
            gr.Dropdown(["Butler", "Gatstamper", "Gatvuller", "Gatswaai", "Codex", "Chaos"], label="Archetype"),
            gr.Slider(4, 16, step=4, label="Bars"),
            gr.Slider(10, 18, label="Syllables/Bar")
        ],
        outputs=gr.Textbox(label="Verse"),
        title="House Codex - Lyrical Engine",
        description="Phonetic/Rhythmic Object System for sovereign lyric generation"
    )
    demo.launch()