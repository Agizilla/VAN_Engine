from typing import List, Tuple
import random
from lexicon_engine import LexiconVault, PhoneticWord

GATVULLER_PHASE = "Gatvuller"     # Bars 1-3: Problem/Hole - Work narrative, filler tags
GATSTAMPER_PHASE = "Gatstamper"  # Bars 4-6: Build/Harden - high energy, high plosives
GATVEER_PHASE = "Gatveer"       # Bars 7-8: Polish/Sweep - low energy, smooth

class NarrativeContext:
    def __init__(self, archetype: str, narrative_bucket: str):
        self.archetype = archetype
        self.narrative_bucket = narrative_bucket
        self.previous_words: List[PhoneticWord] = []
    
    def select_glue_word(self, vault: LexiconVault, syllables_needed: int, language: str) -> PhoneticWord:
        candidates = vault.get_compatible_glue(self.narrative_bucket, syllables_needed)
        if not candidates:
            candidates = vault.get_compatible_glue("Library", syllables_needed)
        if candidates and self.previous_words:
            prev_energy = self.previous_words[-1].energy_score
            best = min(candidates, key=lambda g: abs(vault.words[g.token].energy_score - prev_energy))
            return best
        return random.choice(candidates) if candidates else None

class VerseBuilder:
    def __init__(self, vault: LexiconVault, archetype: str, bpm: int = 140):
        from rhythm_generator import RhythmSkeleton
        self.vault = vault
        self.skeleton = RhythmSkeleton(vault, bpm)
        self.narrative = NarrativeContext(archetype, self._infer_bucket(archetype))
    
    def _infer_bucket(self, archetype: str) -> str:
        mapping = {
            "Gatvuller": "Work", "Gatstamper": "Work", "Gatveer": "Work",
            "Butler": "Library", "Codex": "Library", "Chaos": "Street"
        }
        return mapping.get(archetype, "Library")
    
    def _get_phase(self, bar_num: int, total_bars: int) -> str:
        """Determine which Gat phase this bar belongs to."""
        normalized = bar_num / total_bars
        if normalized < 0.375:
            return GATVULLER_PHASE
        elif normalized < 0.75:
            return GATSTAMPER_PHASE
        else:
            return GATVEER_PHASE
    
    def _get_phase_priority(self, phase: str) -> dict:
        """Get filtering priorities for each Gat phase."""
        if phase == GATVULLER_PHASE:
            return {
                "narrative_bucket": "Work",
                "min_energy": 0.0, "max_energy": 0.5,
                "min_plosives": 0, "max_plosives": 2,
                "prefer_tags": ["filler", "problem", "hole"]
            }
        elif phase == GATSTAMPER_PHASE:
            return {
                "narrative_bucket": "Work",
                "min_energy": 0.6, "max_energy": 1.0,
                "min_plosives": 1, "max_plosives": 5,
                "prefer_tags": ["industrial", "builder", "percussive", "chaos"]
            }
        else:  # GATVEER_PHASE
            return {
                "narrative_bucket": "Library",
                "min_energy": 0.0, "max_energy": 0.4,
                "min_plosives": 0, "max_plosives": 1,
                "prefer_tags": ["smooth", "finish", "spiritual", "knowledge"]
            }
    
    def _fill_bar_for_phase(self, bar_num: int, total_bars: int,
                         target_spb: float, language: str = "english") -> Tuple[List[PhoneticWord], str]:
        """Fill a bar with words optimized for the current Gat phase."""
        phase = self._get_phase(bar_num, total_bars)
        priority = self._get_phase_priority(phase)
        selected = []
        remaining = int(target_spb)
        
        while remaining > 0:
            candidates = self._get_phase_candidates(priority, language, remaining)
            if not candidates:
                candidates = self.vault.find_by_syllables(min(remaining, 3), language)
            if not candidates:
                candidates = list(self.vault.words.values())
            
            if candidates:
                word = random.choice(candidates)
                selected.append(word)
                remaining -= word.syllables
            else:
                break
        
        flow = self._generate_flow_for_phase(selected, phase)
        return selected, flow
    
    def _get_phase_candidates(self, priority: dict, language: str, 
                           max_syllables: int) -> List[PhoneticWord]:
        """Get words matching phase priorities."""
        candidates = []
        for word in self.vault.words.values():
            if word.language != language:
                continue
            if word.syllables > max_syllables:
                continue
            if not (priority["min_energy"] <= word.energy_score <= priority["max_energy"]):
                continue
            if not (priority["min_plosives"] <= word.plosive_count <= priority["max_plosives"]):
                continue
            if priority.get("prefer_tags"):
                if any(tag in word.tags for tag in priority["prefer_tags"]):
                    candidates.append(word)
            else:
                candidates.append(word)
        return candidates
    
    def _generate_flow_for_phase(self, words: List[PhoneticWord], phase: str) -> str:
        """Generate flow guide based on Gat phase."""
        if phase == GATVULLER_PHASE:
            return "Slow, contemplative - describe the hole/gap (Bars 1-3)"
        elif phase == GATSTAMPER_PHASE:
            return "Hard, percussive slam - build and compact (Bars 4-6)"
        else:
            return "Smooth melodic flow - polish and finish (Bars 7-8)"
    
    def build_verse(self, bars: int = 8, mandatory_tokens: List[str] = None,
                   spb: float = 14.0) -> List[Tuple[List[PhoneticWord], str]]:
        """Build full verse using Gat Lifecycle Loop."""
        verse = []
        mandatory_tokens = mandatory_tokens or []
        
        for bar_num in range(bars):
            tokens_this_bar = []
            if bar_num == 0 and mandatory_tokens:
                tokens_this_bar = [mandatory_tokens[0]]
            elif bar_num == bars - 1 and len(mandatory_tokens) > 1:
                tokens_this_bar = [mandatory_tokens[1:]]
            
            if tokens_this_bar:
                words, flow = self.skeleton.fill_bar(
                    tokens_this_bar, target_spb=spb, language="english"
                )
            else:
                words, flow = self._fill_bar_for_phase(bar_num, bars, spb)
            
            verse.append((words, flow))
            self.narrative.previous_words = words
        
        return verse

class GatLifecycle:
    """High-level controller for the 3-stage Gat lifecycle."""
    def __init__(self, vault: LexiconVault, base_archetype: str = "Gatstamper"):
        self.vault = vault
        self.base_archetype = base_archetype
        self.builder = VerseBuilder(vault, base_archetype)
    
    def generate(self, bars: int = 8, spb: float = 14.0) -> dict:
        """Generate complete verse with lifecycle metadata."""
        verse = self.builder.build_verse(bars=bars, spb=spb)
        
        result = {
            "total_bars": bars,
            "spb": spb,
            "phases": {
                "Gatvuller": {"bars": "1-3", "theme": "Problem/Hole"},
                "Gatstamper": {"bars": "4-6", "theme": "Build/Harden"},
                "Gatveer": {"bars": "7-8", "theme": "Polish/Finish"}
            },
            "verse": []
        }
        
        for bar_idx, (words, flow) in enumerate(verse, 1):
            phase = self.builder._get_phase(bar_idx - 1, bars)
            result["verse"].append({
                "bar": bar_idx,
                "phase": phase,
                "words": [w.token for w in words],
                "flow": flow
            })
        
        return result
    
    def to_markdown(self, verse_data: dict) -> str:
        """Convert verse to markdown format."""
        lines = ["# Gat Lifecycle Verse", ""]
        
        for phase in [GATVULLER_PHASE, GATSTAMPER_PHASE, GATVEER_PHASE]:
            phase_info = verse_data["phases"][phase]
            lines.append(f"## {phase} ({phase_info['bars']})")
            lines.append(f"*{phase_info['theme']}*")
            lines.append("")
            
            for bar in verse_data["verse"]:
                if bar["phase"] == phase:
                    words_str = " ".join(bar["words"])
                    lines.append(f"**Bar {bar['bar']}**: {words_str}")
            lines.append("")
        
        return "\n".join(lines)