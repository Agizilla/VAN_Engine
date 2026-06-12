import json
import os

def export_to_markdown(lexicon_data, output_path="lexicon_export.md"):
    """Export lexicon to Markdown table format"""
    md_lines = ["# Lyrical Engine Lexicon", "", "| Token | ARPAbet | IPA | Syllables | Stress | Plosives | Fricatives | Archetype |", "|---|---|---|---|---|---|---|---|"]
    
    for entry in lexicon_data:
        md_lines.append(f"| {entry['token']} | {entry['phonemes']} | {entry['ipa']} | {entry['syllables']} | {entry['stress_pattern']} | {entry['plosive_count']} | {entry['fricative_count']} | {entry['archetype']} |")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    return output_path

def export_to_audio_sync(lexicon_data, output_path="audio_sync.json"):
    """Export lexicon for audio sync (beat grid + phoneme timing)"""
    audio_sync = {
        "version": "1.0",
        "grid": {
            "bpm": 140,
            "time_signature": "4/4",
            "spb": 14
        },
        "tokens": []
    }
    
    for entry in lexicon_data:
        token_entry = {
            "word": entry["token"],
            "phonemes": entry["phonemes"].split(),
            "ipa": entry["ipa"],
            "syllables": entry["syllables"],
            "stress": list(entry["stress_pattern"]),
            "energy": entry["energy_score"],
            "archetype": entry["archetype"],
            "tags": entry["tags"],
            "beats": entry["syllables"]
        }
        audio_sync["tokens"].append(token_entry)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audio_sync, f, indent=2)
    
    return output_path

def export_to_csv(lexicon_data, output_path="lexicon_export.csv"):
    """Export to CSV for spreadsheet analysis"""
    lines = ["token,phonemes,ipa,syllables,stress,plosives,fricatives,energy,rhyme_family,archetype"]
    
    for entry in lexicon_data:
        lines.append(f"{entry['token']},{entry['phonemes']},{entry['ipa']},{entry['syllables']},{entry['stress_pattern']},{entry['plosive_count']},{entry['fricative_count']},{entry['energy_score']},{entry['rhyme_family']},{entry['archetype']}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return output_path

def export_all_formats(lexicon_path="lexicon.json", min_tokens=50):
    """Export all formats"""
    with open(lexicon_path, encoding="utf-8") as f:
        data = json.load(f)
    
    lexicon = data.get("lexicon", [])
    
    if len(lexicon) < min_tokens:
        print(f"[!] Skipping: only {len(lexicon)} tokens (need {min_tokens})")
        return
    
    print(f"[*] Exporting {len(lexicon)} tokens...")
    
    md_path = export_to_markdown(lexicon)
    print(f"[OK] Markdown: {md_path}")
    
    json_path = export_to_audio_sync(lexicon)
    print(f"[OK] Audio Sync: {json_path}")
    
    csv_path = export_to_csv(lexicon)
    print(f"[OK] CSV: {csv_path}")
    
    return md_path, json_path, csv_path

if __name__ == "__main__":
    os.chdir(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\OfflineSongWriter")
    export_all_formats()