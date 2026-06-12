#!/usr/bin/env python3
"""
Migrate old-format artists.json to Universal Music Artist Lexicon format.
Usage: python migrate_to_lexicon.py [artists.json] [output.json]
"""

import json
import uuid
from pathlib import Path

LEXICON_TEMPLATE = {
    "version": "1.0.0",
    "last_updated": "2026-01-15T10:00:00Z",
    "artist_count": 0,
    "artists": {},
    "indexes": {
        "by_name": {},
        "by_slug": {},
        "by_genre": {},
        "by_vocal_type": {},
        "by_era": {},
    },
    "global_settings": {
        "default_audio_path": "./Audio/",
        "default_cache_path": "./cache/",
        "genius_api_token": "env:GENIUS_TOKEN",
        "preferred_tts_engine": "google",
    },
}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")


def migrate_artists(old_json_path: str, output_path: str = "music_lexicon.json") -> dict:
    with open(old_json_path, "r", encoding="utf-8") as f:
        old_artists = json.load(f)

    lexicon = dict(LEXICON_TEMPLATE)

    for old_artist in old_artists:
        artist_id = str(uuid.uuid4())[:8]
        slug = slugify(old_artist["name"])

        collaborations = []
        for collab in old_artist.get("collaborations", []):
            if collab.get("artist"):
                collaborations.append({
                    "with_artist_name": collab["artist"],
                    "with_artist_id": None,
                    "type": "feature",
                    "songs": [{
                        "title": collab.get("song", "TBD"),
                        "year": collab.get("year", "TBD"),
                        "role": "featured",
                        "lyrics_snippet": collab.get("lyrics_snippet", ""),
                    }],
                })

        recommended = []
        for rec in old_artist.get("recommended", []):
            recommended.append({
                "artist_name": rec.get("artist", ""),
                "artist_id": None,
                "reason": "AI suggested",
                "score": 0.7,
                "suggested_song_style": "collaboration track",
            })

        artist_obj = {
            "id": artist_id,
            "name": old_artist["name"],
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
                "profile_pic": old_artist.get("profile_pic",
                    f"https://ui-avatars.com/api/?name={old_artist['name'].replace(' ', '+')}&size=200&background=random"),
                "banner": None,
                "color_palette": [],
            },
            "external_ids": {},
            "tags": [],
            "notes": "",
        }

        lexicon["artists"][artist_id] = artist_obj
        lexicon["indexes"]["by_name"][old_artist["name"]] = artist_id
        lexicon["indexes"]["by_slug"][slug] = artist_id

    lexicon["artist_count"] = len(lexicon["artists"])

    # Build genre index
    for aid, artist in lexicon["artists"].items():
        for genre in artist["metadata"]["genres"]:
            if genre not in lexicon["indexes"]["by_genre"]:
                lexicon["indexes"]["by_genre"][genre] = []
            lexicon["indexes"]["by_genre"][genre].append(aid)

    # Build vocal type index
    for aid, artist in lexicon["artists"].items():
        vt = artist["metadata"]["vocal_type"]
        if vt not in lexicon["indexes"]["by_vocal_type"]:
            lexicon["indexes"]["by_vocal_type"][vt] = []
        lexicon["indexes"]["by_vocal_type"][vt].append(aid)

    # Build era index
    for aid, artist in lexicon["artists"].items():
        era = artist["metadata"]["era"]
        if era not in lexicon["indexes"]["by_era"]:
            lexicon["indexes"]["by_era"][era] = []
        lexicon["indexes"]["by_era"][era].append(aid)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=2, ensure_ascii=False)

    print(f"Migrated {len(old_artists)} artists to {output_path}")
    return lexicon


def add_genre_index(lexicon_path: str):
    """Rebuild genre index after manual edits."""
    with open(lexicon_path, "r", encoding="utf-8") as f:
        lexicon = json.load(f)

    index = {}
    for aid, artist in lexicon["artists"].items():
        for genre in artist["metadata"]["genres"]:
            index.setdefault(genre, []).append(aid)
    lexicon["indexes"]["by_genre"] = index

    with open(lexicon_path, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=2, ensure_ascii=False)

    print(f"Rebuilt genre index for {len(lexicon['artists'])} artists")


def merge_lexicons(base_path: str, incoming_path: str, output_path: str = None):
    """Merge incoming artists into an existing lexicon (no duplicates by slug)."""
    with open(base_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    with open(incoming_path, "r", encoding="utf-8") as f:
        inc = json.load(f)

    existing_slugs = {a["slug"] for a in base["artists"].values()}
    merged = 0

    for aid, artist in inc["artists"].items():
        if artist["slug"] not in existing_slugs:
            new_id = str(uuid.uuid4())[:8]
            base["artists"][new_id] = artist
            base["artists"][new_id]["id"] = new_id
            base["indexes"]["by_name"][artist["name"]] = new_id
            base["indexes"]["by_slug"][artist["slug"]] = new_id
            existing_slugs.add(artist["slug"])
            merged += 1

    base["artist_count"] = len(base["artists"])
    output = output_path or base_path
    with open(output, "w", encoding="utf-8") as f:
        json.dump(base, f, indent=2, ensure_ascii=False)

    print(f"Merged {merged} new artists into {output}")
    return base


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  migrate artists.json [output.json]  -- migrate old format to lexicon")
        print("  merge base.json incoming.json         -- merge two lexicons")
        print("  reindex lexicon.json                 -- rebuild genre index")
        sys.exit(1)

    if args[0] == "merge" and len(args) >= 3:
        merge_lexicons(args[1], args[2], args[3] if len(args) > 3 else None)
    elif args[0] == "reindex":
        add_genre_index(args[1])
    else:
        migrate_artists(args[0], args[1] if len(args) > 1 else "music_lexicon.json")
