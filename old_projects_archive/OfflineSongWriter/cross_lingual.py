from typing import List, Tuple
from lexicon_engine import LexiconVault, PhoneticWord

class ArchetypeTranslator:
    """Translates across languages by preserving archetype, not semantics"""
    
    def __init__(self, vault: LexiconVault):
        self.vault = vault
        self.archetype_map = {
            "motion": ["Gatswaai", "flow", "ride"],
            "chaos": ["Gattapatatta", "breakdown", "turbulence"],
            "spiritual": ["Codex", "scripture", "vessel"],
            "industrial": ["Gatstamper", "compress", "forge"]
        }
    
    def translate_verse(self, 
                       english_verse: List[Tuple[List[PhoneticWord], str]],
                       target_language: str = "afrikaans") -> List[Tuple[List[PhoneticWord], str]]:
        """
        Translate verse from English to Afrikaans by:
        1. Identifying function (archetype) of each word
        2. Finding equivalent archetype in target language
        3. Re-fit to rhythm
        """
        translated = []
        
        for words, flow_guide in english_verse:
            new_words = []
            
            for word in words:
                # Step A: Identify function
                function = self._identify_function(word)
                
                # Step B: Find equivalent archetype in target language
                equivalent = self.vault.find_by_archetype(function)
                equivalent = [w for w in equivalent if w.language == target_language]
                
                # Step C: Pick best match (same syllables if possible)
                if equivalent:
                    best = min(equivalent,
                              key=lambda w: abs(w.syllables - word.syllables))
                    new_words.append(best)
                else:
                    new_words.append(word)  # Fallback: keep original
            
            translated.append((new_words, flow_guide))
        
        return translated
    
    def _identify_function(self, word: PhoneticWord) -> str:
        """What does this word DO in the narrative?"""
        # Match tags to functions
        if "motion" in word.tags:
            return "Gatswaai"
        elif "chaos" in word.tags:
            return "Gattapatatta"
        elif "spiritual" in word.tags:
            return "Codex"
        else:
            return word.archetype