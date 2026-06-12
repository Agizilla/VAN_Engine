import random
import json

class HouseCodexEngine:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.active_context = None
        self.alliteration_target = None
        self.phase_weights = {
            "Gatvuller": {"Chaos": 1.0, "Codex": 0.05},
            "Gatstamper": {"Codex": 1.0, "Chaos": 0.05}
        }
        
        self.rhyme_clusters = {
            "tech": ["code", "node", "load", "mode", "road", "codex", "node", "abode"],
            "void": ["chasm", "spasm", "phantom", "atom", "entropy", "symptom"],
            "flow": ["glide", "guide", "slide", "tide", "wide", "side", "ride"],
            "crush": ["breach", "reach", "leech", "speech", "beach", "teach"],
            "storm": ["form", "norm", "storm", "transform", "conform", "inform"],
            "light": ["fight", "height", "sight", "might", "right", "tight"]
        }
    
    def _get_syllables(self, word_data):
        return word_data.get("syllables", max(1, len(word_data.get("token", "")) // 3))
    
    def _calculate_weight(self, word_data, phase, target_spb):
        weight = 10.0
        token = word_data.get("token", "").lower()
        archetype = word_data.get("archetype", "Codex")
        tags = word_data.get("tags", [])
        
        if self.active_context in tags:
            weight *= 4.0
        
        if self.alliteration_target and token.startswith(self.alliteration_target):
            weight *= 2.0
        
        phase_penalty = self.phase_weights.get(phase, {}).get(archetype, 0.1)
        if phase_penalty < 1.0:
            weight *= phase_penalty
        
        energy = word_data.get("energy_score", 0.3)
        weight *= (1.0 + energy)
        
        consonants = sum(1 for c in token if c in 'bcdfghjklmnpqrstvwxz')
        weight *= (1.0 + consonants * 0.1)
        
        return weight
    
    def generate_verse(self, archetype, bar_count=8, target_spb=16.0, use_glue=True, couplet_mode=False):
        verse_lines = []
        
        themes = ["digital", "biological", "architectural", "void", "quantum", "neural"]
        self.active_context = random.choice(themes)
        
        cluster_id = random.choice(list(self.rhyme_clusters.keys())) if couplet_mode else None
        rhyme_words = list(self.rhyme_clusters[cluster_id]) if couplet_mode else []
        
        alliteration_letters = "abcdefstkmp"
        
        half = bar_count // 2
        
        for bar_idx in range(bar_count):
            phase = "Gatvuller" if bar_idx < half else "Gatstamper"
            
            if bar_idx % 2 == 0:
                self.alliteration_target = random.choice(alliteration_letters)
            
            current_bar = []
            current_syllables = 0
            
            while current_syllables < target_spb:
                target_archetype = archetype if archetype in ["Chaos", "Codex"] else ("Chaos" if phase == "Gatvuller" else "Codex")
                
                candidates = [
                    w for w in self.lexicon 
                    if w.get("archetype") == target_archetype
                    and self._get_syllables(w) + current_syllables <= target_spb + 1
                ]
                
                if not candidates:
                    candidates = [w for w in self.lexicon if w.get("archetype") == target_archetype][:50]
                
                if not candidates:
                    break
                
                weights = [self._calculate_weight(w, phase, target_spb) for w in candidates]
                
                total_weight = sum(weights)
                if total_weight <= 0:
                    weights = [1.0] * len(candidates)
                
                choice = random.choices(candidates, weights=weights, k=1)[0]
                
                current_bar.append(choice)
                current_syllables += self._get_syllables(choice)
                
                candidates.remove(choice)
                
                if current_syllables >= target_spb:
                    break
            
            if current_bar:
                tokens = [w["token"].lower() for w in current_bar]
                
                if couplet_mode and bar_idx % 2 == 1 and rhyme_words:
                    tokens.append(random.choice(rhyme_words))
                
                if use_glue and random.random() > 0.4 and current_syllables < target_spb - 1:
                    glue = random.choice(["the", "and", "in", "of", "to", "a", "my", "on", "for", "is"])
                    tokens.insert(0, glue)
                    current_syllables += 1
                
                bar_text = " ".join(tokens).capitalize()
                if not bar_text.endswith('.'):
                    bar_text += "."
                
                energy = sum(w.get("energy_score", 0) for w in current_bar) / len(current_bar)
                energy_label = "HIGH" if energy >= 0.6 else "MED" if energy >= 0.3 else "LOW"
                
                verse_lines.append(f"| {str(bar_idx+1).zfill(2)} | [{energy_label}] | {bar_text} |")
        
        return "\n".join(verse_lines)

def create_engine(lexicon_path="lexicon.json"):
    import json
    try:
        with open(lexicon_path, encoding="utf-8") as f:
            data = json.load(f)
            return HouseCodexEngine(data.get("lexicon", []))
    except:
        return HouseCodexEngine([])

if __name__ == "__main__":
    import sys
    engine = create_engine()
    
    archetype = "Chaos"
    bar_count = 4
    target_spb = 14.0
    couplet_mode = False
    
    if len(sys.argv) > 1:
        archetype = sys.argv[1]
    if len(sys.argv) > 2:
        bar_count = int(sys.argv[2])
    if len(sys.argv) > 3:
        target_spb = float(sys.argv[3])
    if len(sys.argv) > 4:
        couplet_mode = sys.argv[4].lower() == "couplet"
    
    result = engine.generate_verse(archetype, bar_count, target_spb, couplet_mode=couplet_mode)
    
    print(f"## V4 Generated Verse ({archetype})")
    if couplet_mode:
        print("## COUPET_MODE_ENABLED")
    print(result)