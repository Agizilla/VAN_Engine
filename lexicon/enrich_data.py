"""
enrich_data.py - Enrich artist data from Genius API, outputting directly to music_lexicon.json format.

Usage: python enrich_data.py RapArtists.xlsx [--output music_lexicon.json]
"""

import json
import os
import random
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import pandas as pd
import requests


GENIUS_API_BASE = "https://api.genius.com"


def get_genius_token() -> Optional[str]:
    token = os.environ.get("GENIUS_TOKEN")
    if token:
        return token
    try:
        with open("genius_token.txt") as f:
            return f.read().strip()
    except FileNotFoundError:
        pass
    print("WARNING: No GENIUS_TOKEN found. Set env var or create genius_token.txt")
    return "YOUR_GENIUS_TOKEN_HERE"


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")


def get_first_n_lines(lyrics: str, n: int = 4) -> str:
    lines = [l.strip() for l in lyrics.split("\n") if l.strip() and not l.startswith("[")]
    return "\n".join(lines[:n])


def search_collaboration(token: str, artist1: str, artist2: str, max_retries: int = 3) -> Optional[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    queries = [
        f"{artist1} {artist2}",
        f"{artist1} {artist2} lyrics",
        f"{artist1} ft {artist2}",
        f"{artist1} feat {artist2}",
        f"{artist2} {artist1}",
    ]
    for query in queries:
        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    f"{GENIUS_API_BASE}/search",
                    headers=headers,
                    params={"q": query},
                    timeout=10,
                )
                if resp.status_code == 429:
                    time.sleep(5)
                    continue
                if resp.status_code != 200:
                    continue
                hits = resp.json().get("response", {}).get("hits", [])
                for hit in hits:
                    result = hit.get("result", {})
                    title = result.get("title", "")
                    primary = result.get("primary_artist", {})
                    primary_name = primary.get("name", "").lower()
                    a1_lower = artist1.lower()
                    a2_lower = artist2.lower()
                    if a1_lower in primary_name or a2_lower in primary_name:
                        snippet = result.get("lyrics_state", "")
                        if snippet == "complete":
                            try:
                                lyrics_resp = requests.get(
                                    f"{GENIUS_API_BASE}/songs/{result['id']}/lyrics",
                                    headers=headers,
                                    timeout=10,
                                )
                                lyrics_snippet = get_first_n_lines(
                                    lyrics_resp.json().get("response", {}).get("lyrics", {}).get("body", {}).get("html", "")
                                ) if lyrics_resp.status_code == 200 else ""
                            except Exception:
                                lyrics_snippet = ""
                        else:
                            lyrics_snippet = ""
                        return {
                            "title": title,
                            "year": result.get("release_date_for_display", "TBD")[-4:]
                            if result.get("release_date_for_display") else "TBD",
                            "lyrics_snippet": lyrics_snippet[:200],
                        }
                time.sleep(random.uniform(0.5, 1.0))
            except requests.RequestException:
                time.sleep(2)
    return None


def enrich_artist_data(excel_path: str, output_path: str = "music_lexicon.json") -> dict:
    token = get_genius_token()
    df = pd.read_excel(excel_path)
    required = {"Artist", "Collaborators", "Recommended"}
    if not required.issubset(df.columns):
        raise ValueError(f"Excel must have columns: {required}")

    lexicon = {
        "version": "1.0.0",
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artist_count": 0,
        "artists": {},
        "indexes": {"by_name": {}, "by_slug": {}, "by_genre": {}, "by_vocal_type": {}, "by_era": {}},
        "global_settings": {
            "default_audio_path": "./Audio/",
            "default_cache_path": "./cache/",
            "genius_api_token": "env:GENIUS_TOKEN",
            "preferred_tts_engine": "google",
        },
    }

    for _, row in df.iterrows():
        artist_name = str(row["Artist"]).strip()
        if not artist_name:
            continue

        aid = str(uuid.uuid4())[:8]
        slug = slugify(artist_name)

        collab_names = [c.strip() for c in str(row.get("Collaborators", "")).split(",") if c.strip()]
        recommended_names = [r.strip() for r in str(row.get("Recommended", "")).split(",") if r.strip()]

        collaborations = []
        print(f"Processing: {artist_name}")
        for cname in collab_names:
            time.sleep(random.uniform(0.5, 2.0))
            found = search_collaboration(token, artist_name, cname)
            if found:
                collaborations.append({
                    "with_artist_name": cname,
                    "with_artist_id": None,
                    "type": "feature",
                    "songs": [{
                        "title": found["title"],
                        "year": found["year"],
                        "role": "featured",
                        "lyrics_snippet": found["lyrics_snippet"],
                    }],
                })
                print(f"  Found: {found['title']} ({found['year']})")
            else:
                collaborations.append({
                    "with_artist_name": cname,
                    "with_artist_id": None,
                    "type": "feature",
                    "songs": [{"title": "TBD", "year": "TBD", "role": "featured", "lyrics_snippet": ""}],
                })
                print(f"  No result for {cname}, using TBD")

        recommended = [
            {"artist_name": r, "artist_id": None, "reason": "AI suggested", "score": 0.7, "suggested_song_style": "collaboration track"}
            for r in recommended_names
        ]

        artist_obj = {
            "id": aid,
            "name": artist_name,
            "slug": slug,
            "aka": [],
            "metadata": {
                "genres": ["hip-hop"],
                "era": "2020s",
                "country": "USA",
                "active_years": {"start": 2015, "end": None},
                "vocal_type": "unknown",
                "vocal_range": "unknown",
            },
            "prosody_profile": {},
            "discography": [],
            "collaborations": collaborations,
            "recommended_collaborations": recommended,
            "samples": {},
            "analysis_cache": {},
            "visual": {
                "profile_pic": f"https://ui-avatars.com/api/?name={artist_name.replace(' ', '+')}&size=200&background=random",
                "banner": None,
                "color_palette": [],
            },
            "external_ids": {},
            "tags": [],
            "notes": "",
        }

        lexicon["artists"][aid] = artist_obj
        lexicon["indexes"]["by_name"][artist_name] = aid
        lexicon["indexes"]["by_slug"][slug] = aid

    lexicon["artist_count"] = len(lexicon["artists"])

    for aid, artist in lexicon["artists"].items():
        for genre in artist["metadata"]["genres"]:
            lexicon["indexes"]["by_genre"].setdefault(genre, []).append(aid)
        vt = artist["metadata"]["vocal_type"]
        lexicon["indexes"]["by_vocal_type"].setdefault(vt, []).append(aid)
        era = artist["metadata"]["era"]
        lexicon["indexes"]["by_era"].setdefault(era, []).append(aid)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Enriched {len(lexicon['artists'])} artists to {output_path}")
    return lexicon


def parse_collaborators(collab_str: str) -> list[str]:
    """Split comma-separated collaborator string, handling edge cases."""
    if not collab_str or collab_str.strip().lower() in ("", "none", "n/a", "tbd"):
        return []
    return [c.strip() for c in collab_str.split(",") if c.strip()]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python enrich_data.py RapArtists.xlsx [--output music_lexicon.json]")
        sys.exit(1)
    excel_path = sys.argv[1]
    output = "music_lexicon.json"
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]
    enrich_artist_data(excel_path, output)
