from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class PhoneticWord:
    token: str
    phonetics: str
    syllables: int
    stress_pattern: str  # e.g., "HL", "LHL"
    rhyme_family: str  # e.g., "aai", "atta"
    tags: List[str]  # ["motion", "percussive", "chaos"]
    energy_score: float  # 0.0-1.0 (1.0 = highly percussive)
    archetype: str  # "Gatvuller", "Gatstamper", "Butler"
    language: str  # "afrikaans" or "english"
    plosive_count: int  # Count of P/T/K/B/D
    
    def syllables_per_beat(self, bpm: int, beats_per_bar: int = 4) -> float:
        """Calculate SPB (Syllables Per Beat)"""
        return self.syllables / beats_per_bar

@dataclass
class GlueWord:
    """Connective words (The, And, In, Die, En, So)"""
    token: str
    syllables: int
    narrative_bucket: str  # "Work", "Library", "Street", "Spiritual"
    language: str

class LexiconVault:
    def __init__(self, lexicon_path: str):
        with open(lexicon_path) as f:
            data = json.load(f)
        
        self.words: Dict[str, PhoneticWord] = {}
        self.glue: Dict[str, List[GlueWord]] = {
            "Work": [], "Library": [], "Street": [], "Spiritual": []
        }
        
        # Load words
        for word_dict in data.get("lexicon", []):
            word = PhoneticWord(**word_dict)
            self.words[word.token] = word
        
        # Load glue words
        for glue_dict in data.get("glue_words", []):
            glue = GlueWord(**glue_dict)
            self.glue[glue.narrative_bucket].append(glue)
    
    def find_by_syllables(self, syllable_count: int, language: str = "english") -> List[PhoneticWord]:
        """Get all words with exact syllable count"""
        return [w for w in self.words.values() 
                if w.syllables == syllable_count and w.language == language]
    
    def find_by_rhyme_family(self, rhyme: str) -> List[PhoneticWord]:
        """Get all words that rhyme"""
        return [w for w in self.words.values() if w.rhyme_family == rhyme]
    
    def find_by_archetype(self, archetype: str) -> List[PhoneticWord]:
        """Get words from specific archetype"""
        return [w for w in self.words.values() if w.archetype == archetype]
    
    def get_compatible_glue(self, narrative_bucket: str, syllables: int) -> List[GlueWord]:
        """Get glue words matching narrative and syllable count"""
        return [g for g in self.glue.get(narrative_bucket, [])
                if g.syllables == syllables]