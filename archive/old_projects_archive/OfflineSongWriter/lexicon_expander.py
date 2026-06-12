"""
Lexicon Expansion Module
Automatically grows lexicon.json using phonetic analysis.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from lexicon_engine import PhoneticWord, LexiconVault

PHONETIC_PATTERNS = {
    "english": {
        "vowels": "aeiouAEIOU",
        "consonants": "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ",
        "plosives": ["p", "t", "k", "b", "d", "g"],
        "fricatives": ["f", "v", "s", "z", "sh", "zh", "th"],
        "sonorants": ["l", "r", "m", "n", "ng", "w", "y"]
    },
    "afrikaans": {
        "vowels": "aeiouäëïöüAEIOUÄËÏÖÜ",
        "consonants": "bcdfghjklmnprstvwxyzBCDFGHJKLMNPRSTVWXYZ",
        "plosives": ["p", "t", "k", "b", "d", "g"],
        "fricatives": ["f", "v", "s", "z", "sh"],
        "sonorants": ["l", "r", "m", "n", "ng", "w", "j"]
    }
}

def analyze_phonetics(word: str, language: str = "english") -> Dict:
    """Extract phonetic properties from a word."""
    patterns = PHONETIC_PATTERNS.get(language, PHONETIC_PATTERNS["english"])
    vowels = patterns["vowels"]
    consonants = patterns["consonants"]
    plosives = patterns["plosives"]
    
    phonetics = ""
    syllables = 0
    in_vowel = False
    stress_pattern = ""
    
    for char in word.lower():
        if char in vowels:
            if not in_vowel:
                syllables += 1
                in_vowel = True
                stress_pattern += "H" if syllables <= 2 else "L"
            phonetics += char
        elif char in consonants:
            in_vowel = False
            phonetics += char
        elif char == "-":
            in_vowel = False
    
    plosive_count = sum(1 for p in plosives if p in word.lower())
    
    return {
        "phonetics": phonetics or word.lower(),
        "syllables": max(1, syllables),
        "stress_pattern": stress_pattern[:min(syllables, 3)],
        "plosive_count": plosive_count
    }

def infer_rhyme_family(word: str) -> str:
    """Infer rhyme family from word ending."""
    word = word.lower().strip("-")
    if len(word) >= 3:
        return word[-3:]
    elif len(word) >= 2:
        return word[-2:]
    return word[-1:] + "a"

def infer_tags(analysis: Dict, context: str = "") -> List[str]:
    """Infer tags based on phonetic analysis."""
    tags = []
    
    if analysis["plosive_count"] >= 3:
        tags.append("percussive")
        tags.append("chaos")
    elif analysis["plosive_count"] >= 1:
        tags.append("industrial")
        tags.append("technical")
    
    if analysis["stress_pattern"].startswith("HL"):
        tags.append("punchy")
        tags.append("rhythmic")
    
    if analysis["syllables"] == 1:
        tags.append("mono")
        tags.append("impact")
    elif analysis["syllables"] >= 3:
        tags.append("flow")
        tags.append("extended")
    
    if "motion" in context.lower():
        tags.append("motion")
    if "spiritual" in context.lower():
        tags.append("spiritual")
    if "work" in context.lower():
        tags.append("work")
    if "street" in context.lower():
        tags.append("street")
    
    return tags or ["generic"]

def infer_archetype(analysis: Dict, tags: List[str]) -> str:
    """Infer archetype from phonetic analysis."""
    if "chaos" in tags or "percussive" in tags:
        return "Chaos"
    elif "spiritual" in tags:
        return "Codex"
    elif "spiritual" in tags or "knowledge" in tags:
        return "Codex"
    elif "industrial" in tags or "technical" in tags:
        return "Gatstamper"
    elif "motion" in tags or "flow" in tags:
        return "Gatswaai"
    elif analysis["energy_score"] > 0.7:
        return "Gatstamper"
    elif analysis["energy_score"] < 0.3:
        return "Codex"
    else:
        return "Butler"

def calculate_energy(analysis: Dict) -> float:
    """Calculate energy score (0.0-1.0) based on phonetics."""
    energy = 0.5
    
    energy += min(analysis["plosive_count"] * 0.1, 0.3)
    
    if analysis["syllables"] == 1:
        energy += 0.1
    elif analysis["syllables"] > 3:
        energy -= 0.1
    
    if analysis["stress_pattern"].startswith("H"):
        energy += 0.1
    
    return max(0.0, min(1.0, energy))

def create_word_from_raw(token: str, language: str = "english", 
                       context: str = "", energy_override: float = None) -> PhoneticWord:
    """Create a PhoneticWord from raw text input."""
    analysis = analyze_phonetics(token, language)
    tags = infer_tags(analysis, context)
    energy = energy_override if energy_override else calculate_energy(analysis)
    
    return PhoneticWord(
        token=token,
        phonetics=analysis["phonetics"],
        syllables=analysis["syllables"],
        stress_pattern=analysis["stress_pattern"],
        rhyme_family=infer_rhyme_family(token),
        tags=tags,
        energy_score=energy,
        archetype=infer_archetype(analysis, tags),
        language=language,
        plosive_count=analysis["plosive_count"]
    )

class LexiconExpander:
    """Automatically expands lexicon with new words."""
    
    def __init__(self, lexicon_path: str = "lexicon.json"):
        self.lexicon_path = Path(lexicon_path)
        self.vault = LexiconVault(str(self.lexicon_path))
    
    def add_words_from_text(self, text: str, language: str = "english") -> int:
        """Extract and add words from raw text."""
        words = re.findall(r'[a-zA-ZäëïöüÄËÏÖÜ]+', text.lower())
        added = 0
        
        existing_tokens = {w.token.lower() for w in self.vault.words.values()}
        
        for word in set(words):
            if word not in existing_tokens and len(word) >= 2:
                try:
                    phonetic_word = create_word_from_raw(word, language)
                    if phonetic_word.syllables <= 5:
                        self.vault.words[phonetic_word.token] = phonetic_word
                        added += 1
                except:
                    continue
        
        return added
    
    def add_from_file(self, file_path: str, language: str = "english") -> int:
        """Add words from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.add_words_from_text(text, language)
    
    def save(self, output_path: str = None):
        """Save expanded lexicon to JSON."""
        output = Path(output_path) if output_path else self.lexicon_path
        
        lexicon_list = []
        for word in self.vault.words.values():
            lexicon_list.append({
                "token": word.token,
                "phonetics": word.phonetics,
                "syllables": word.syllables,
                "stress_pattern": word.stress_pattern,
                "rhyme_family": word.rhyme_family,
                "tags": word.tags,
                "energy_score": word.energy_score,
                "archetype": word.archetype,
                "language": word.language,
                "plosive_count": word.plosive_count
            })
        
        data = {
            "lexicon": lexicon_list,
            "glue_words": [
                {"token": g.token, "syllables": g.syllables, 
                 "narrative_bucket": g.narrative_bucket, "language": g.language}
                for bucket in self.vault.glue.values()
                for g in bucket
            ]
        }
        
        output.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def generate_report(self) -> str:
        """Generate expansion report."""
        by_lang = {"english": 0, "afrikaans": 0}
        by_archetype = {}
        by_energy = {"low": 0, "medium": 0, "high": 0}
        
        for word in self.vault.words.values():
            by_lang[word.language] = by_lang.get(word.language, 0) + 1
            by_archetype[word.archetype] = by_archetype.get(word.archetype, 0) + 1
            
            if word.energy_score < 0.4:
                by_energy["low"] += 1
            elif word.energy_score < 0.7:
                by_energy["medium"] += 1
            else:
                by_energy["high"] += 1
        
        lines = ["# Lexicon Expansion Report", "", "## By Language"]
        for lang, count in by_lang.items():
            lines.append(f"- {lang}: {count}")
        
        lines.append("")
        lines.append("## By Archetype")
        for arch, count in by_archetype.items():
            lines.append(f"- {arch}: {count}")
        
        lines.append("")
        lines.append("## By Energy")
        for level, count in by_energy.items():
            lines.append(f"- {level}: {count}")
        
        return "\n".join(lines)