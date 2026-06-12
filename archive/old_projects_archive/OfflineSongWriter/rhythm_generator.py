from typing import List, Tuple, Dict
import random
from lexicon_engine import LexiconVault, PhoneticWord

class BarTemplate:
    """Defines the rhythmic "shape" of a bar"""
    def __init__(self, max_syllables: int, rhyme_anchor_beat: int = 4):
        self.max_syllables = max_syllables
        self.rhyme_anchor_beat = rhyme_anchor_beat
        self.slots = self._create_slots()
    
    def _create_slots(self) -> List[Dict]:
        """Divide bar into 16th-note slots"""
        # 4 beats × 4 sixteenth notes = 16 slots
        return [
            {"beat": 1, "position": i, "is_power_beat": i == 0}
            for i in range(16)
        ]
    
    def get_rhyme_anchor_syllables(self) -> int:
        """How many syllables should rhyme anchor consume?"""
        # For a 16-syllable bar, last 3-4 syllables form the rhyme
        return max(3, self.max_syllables // 4)

class RhythmSkeleton:
    """Builds bars without semantic meaning—pure syllable fit"""
    def __init__(self, vault, bpm: int = 140):
        self.vault = vault
        self.bpm = bpm
    
    def fill_bar(self, 
                 mandatory_tokens: List[str],
                 target_spb: float = 14.0,
                 language: str = "english") -> Tuple[List[PhoneticWord], str]:
        """
        Fill a bar with words matching SPB constraint.
        
        Args:
            mandatory_tokens: Words that MUST appear
            target_spb: Syllables per bar (e.g., 14-16 for Chopper)
            language: "english" or "afrikaans"
        
        Returns:
            (list of words, flow_guide)
        """
        bar_template = BarTemplate(max_syllables=int(target_spb))
        selected_words = []
        total_syllables = 0
        
        # Step 1: Place mandatory tokens at power beats
        for token in mandatory_tokens:
            if token in self.vault.words:
                word = self.vault.words[token]
                selected_words.append(word)
                total_syllables += word.syllables
        
        # Step 2: Fill remaining syllables
        remaining = int(target_spb) - total_syllables
        while remaining > 0:
            # Get a word that fits
            candidates = self.vault.find_by_syllables(min(remaining, 3), language)
            if not candidates:
                # Fallback: get shorter word
                candidates = self.vault.find_by_syllables(1, language)
            
            if candidates:
                word = random.choice(candidates)
                selected_words.append(word)
                remaining -= word.syllables
            else:
                break
        
        # Step 3: Generate flow guide
        flow_guide = self._generate_flow_guide(selected_words)
        
        return selected_words, flow_guide
    
    def _generate_flow_guide(self, words: List[PhoneticWord]) -> str:
        """Create delivery instructions"""
        avg_energy = sum(w.energy_score for w in words) / len(words) if words else 0
        
        if avg_energy > 0.8:
            return "Fast staccato on beats 2 and 4 (Percussive slam)"
        elif avg_energy > 0.5:
            return "Medium pace with emphasis on power beats"
        else:
            return "Smooth, flowing delivery with melodic rise"