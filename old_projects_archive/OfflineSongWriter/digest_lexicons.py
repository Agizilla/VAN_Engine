import json
import re
import os

class PhoneticDigester:
    def __init__(self):
        self.plosives = set('ptkbdgPTKBDG')
        self.fricatives = set('fvshzFVSHZ')
        self.vowels = set('aeiouyAEIOUY')
        
        self.arpabet_to_ipa = {
            'P': 'p', 'B': 'b', 'T': 't', 'D': 'd', 'K': 'k', 'G': 'ɡ',
            'CH': 'tʃ', 'JH': 'dʒ', 'F': 'f', 'V': 'v', 'TH': 'θ', 'DH': 'ð',
            'S': 's', 'Z': 'z', 'SH': 'ʃ', 'ZH': 'ʒ', 'HH': 'h', 'M': 'm',
            'N': 'n', 'NG': 'ŋ', 'L': 'l', 'R': 'r', 'W': 'w', 'Y': 'j',
            'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ', 'AY': 'aɪ',
            'EH': 'ɛ', 'ER': 'ɜ', 'EY': 'eɪ', 'IH': 'ɪ', 'IY': 'i', 'OW': 'oʊ',
            'OY': 'ɔɪ', 'UH': 'ʊ', 'UW': 'u', 'AO': 'ɔ'
        }
        
        self.use_pronouncing = False
        self.pronouncing = None
        
        try:
            import pronouncing
            self.pronouncing = pronouncing
            self.use_pronouncing = True
            print("[OK] Using pronouncing library (CMU Dict)")
        except ImportError:
            print("[INFO] pronouncing not available, using manual estimation")

    def get_pronouncing_data(self, word):
        if not self.use_pronouncing:
            return None
        try:
            phones = self.pronouncing.phones_for_word(word.lower())
            if phones:
                return {
                    'phonemes': phones[0],
                    'syllables': self.pronouncing.syllable_count(phones[0]),
                    'stress': self.pronouncing.stresses(phones[0]) or '0' * self.pronouncing.syllable_count(phones[0])
                }
        except:
            pass
        return None

    def get_plosive_count(self, phonemes):
        plosive_set = {'P', 'B', 'T', 'D', 'K', 'G'}
        clean = ''.join([c for c in phonemes if not c.isdigit() and c != ' '])
        return sum(1 for p in clean if p in plosive_set)

    def get_syllables_manual(self, word):
        word = word.lower()
        syllables = 0
        prev_was_vowel = False
        vowels = set('aeiouy')
        
        i = 0
        while i < len(word):
            is_vowel = word[i] in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
            i += 1
        
        if word.endswith('e') and syllables > 1:
            syllables -= 1
            
        corrections = {
            'chaos': 2, 'anarchy': 3, 'axiom': 3, 'medium': 3,
            'catastrophe': 4, 'hierarchy': 4, 'architecture': 5
        }
        if word in corrections:
            syllables = corrections[word]
            
        return max(1, syllables)

    def get_stress_manual(self, syllables):
        if syllables == 1: return "1"
        if syllables == 2: return "10"
        return "1" + "0" * (syllables - 1)

    def to_ipa(self, arpabet_str):
        """Convert ARPAbet to IPA representations"""
        if not arpabet_str:
            return ""
        
        phones = arpabet_str.split()
        ipa_segments = []
        
        for phone in phones:
            clean = ''.join([c for c in phone if not c.isdigit()])
            if clean in self.arpabet_to_ipa:
                ipa_segments.append(self.arpabet_to_ipa[clean])
            else:
                ipa_segments.append(clean.lower())
        
        return ''.join(ipa_segments)

    def to_arpabet(self, word):
        manual_overrides = {
            'chaos': 'K EY AA S',
            'axiom': 'AE K S IY AH M',
            'anarchy': 'AE N ER K IY',
            'aberration': 'AE B ER EY SH AH N',
            'algorithm': 'AE L G ER IH TH M',
            'acclaim': 'AE K L EY M',
            'catastrophe': 'K AE T AE S T R OW F IY',
            'codex': 'K OW D EH K S',
        }
        if word.lower() in manual_overrides:
            return manual_overrides[word.lower()]
        
        word = word.lower()
        arpabet = []
        i = 0
        diphthongs = {'ai': 'EY', 'ay': 'EY', 'ei': 'IY', 'ey': 'IY', 'oi': 'OY', 'oy': 'OY', 'ou': 'AW', 'ow': 'AW'}
        
        while i < len(word):
            matched = False
            for dip in sorted(diphthongs, key=len, reverse=True):
                if word[i:].startswith(dip):
                    arpabet.append(diphthongs[dip])
                    i += len(dip)
                    matched = True
                    break
            if not matched:
                char = word[i]
                if char == 'c':
                    arpabet.append('K')
                elif char == 's' and i+1 < len(word) and word[i+1] == 'h':
                    arpabet.append('SH')
                    i += 1
                elif char in self.vowels:
                    arpabet.append(char.upper())
                elif char.isalpha():
                    arpabet.append(char.upper())
                i += 1
        return ' '.join(arpabet) if arpabet else word.upper()

    def get_rhyme_family(self, word):
        word = word.lower().strip("-")
        for ending in ['tion', 'sion', 'ous', 'ious', 'ive', 'ent', 'ant', 'ance', 'ence', 'y']:
            if word.endswith(ending):
                return ending
        return word[-3:] if len(word) >= 3 else word

    def calculate_energy(self, word, plosives, syllables):
        score = (plosives * 0.15) + (sum(1 for c in word.lower() if c in self.fricatives) * 0.08)
        if syllables == 1: score += 0.1
        return round(min(1.0, score), 2)

    def digest_file(self, filename, archetype_name, tags):
        tokens = []
        seen = set()
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    match = re.search(r'[a-zA-Z]+', line)
                    if not match:
                        continue
                    
                    word = match.group().capitalize()
                    if word.lower() in seen:
                        continue
                    seen.add(word.lower())
                    
                    data = self.get_pronouncing_data(word)
                    
                    if data:
                        syllables = data['syllables']
                        phonemes = data['phonemes']
                        stress = data['stress']
                        plosives = self.get_plosive_count(phonemes)
                    else:
                        syllables = self.get_syllables_manual(word)
                        phonemes = self.to_arpabet(word)
                        stress = self.get_stress_manual(syllables)
                        plosives = self.get_plosive_count(phonemes)
                    
                    tokens.append({
                        "token": word,
                        "phonemes": phonemes,
                        "ipa": self.to_ipa(phonemes),
                        "vowel_core": '-'.join([c for c in phonemes if c in 'AEIOU' or c.islower()]),
                        "syllables": syllables,
                        "stress_pattern": stress,
                        "rhyme_family": self.get_rhyme_family(word),
                        "tags": tags,
                        "energy_score": self.calculate_energy(word, plosives, syllables),
                        "archetype": archetype_name,
                        "language": "english",
                        "plosive_count": plosives,
                        "fricative_count": sum(1 for c in word.lower() if c in self.fricatives)
                    })
        except FileNotFoundError:
            print(f"Warning: {filename} not found.")
        
        return tokens

if __name__ == "__main__":
    base_dir = r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\OfflineSongWriter"
    os.chdir(base_dir)
    
    digester = PhoneticDigester()
    
    chaos_tokens = digester.digest_file(
        "chaos_lexicon.txt", 
        "Chaos",
        ["chaos", "disorder", "conflict", "decay"]
    )
    
    codex_tokens = digester.digest_file(
        "codex_lexicon.txt", 
        "Codex",
        ["knowledge", "information", "wisdom", "structure"]
    )
    
    gatswaai_tokens = digester.digest_file(
        "gatswaai_lexicon.txt",
        "Gatswaai",
        ["flow", "lyricism", "craft", "style"]
    )
    
    full_lexicon = chaos_tokens + codex_tokens + gatswaai_tokens
    
    with open("lexicon.json", "w", encoding="utf-8") as f:
        json.dump({"lexicon": full_lexicon, "glue_words": []}, f, indent=2)
    
    print(f"\n[OK] Chaos: {len(chaos_tokens)} tokens")
    print(f"[OK] Codex: {len(codex_tokens)} tokens")
    print(f"[OK] Gatswaai: {len(gatswaai_tokens)} tokens")
    print(f"[OK] Total: {len(full_lexicon)} tokens")
    
    print("\n--- Verification ---")
    for word in ["Chaos", "Axiom", "Anarchy", "Algorithm", "Codex", "Gatswaai"]:
        for t in full_lexicon:
            if t["token"].lower() == word.lower():
                print(f"{t['token']}: syl={t['syllables']}, stress={t['stress_pattern']}, plosives={t['plosive_count']}, phonemes={t['phonemes']}")
                break