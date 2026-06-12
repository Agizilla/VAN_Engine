"""
MusicLexicon — shared data access layer for ClawDia, Lyrics Studio, Beat Reproducer.
Loads the universal music_lexicon.json and provides query methods.

Usage:
    from lexicon.music_lexicon import MusicLexicon
    lexicon = MusicLexicon()
    artist = lexicon.get_artist_by_name("Eminem")
    collabs = lexicon.get_collaborations("Eminem")
    by_genre = lexicon.get_artists_by_genre("hip-hop")
"""

import json
from pathlib import Path
from typing import Any, Optional


LEXICON_PATH = Path(__file__).resolve().parent / "music_lexicon.json"


class MusicLexicon:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or LEXICON_PATH)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return self._empty()
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _empty() -> dict:
        return {
            "version": "1.0.0",
            "artist_count": 0,
            "artists": {},
            "indexes": {"by_name": {}, "by_slug": {}, "by_genre": {}, "by_vocal_type": {}, "by_era": {}},
            "global_settings": {},
        }

    def save(self, path: Optional[str] = None):
        out = Path(path or self.path)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def count(self) -> int:
        return self._data.get("artist_count", 0)

    @property
    def artist_ids(self) -> list[str]:
        return list(self._data["artists"].keys())

    def get_artist(self, artist_id: str) -> Optional[dict]:
        return self._data["artists"].get(artist_id)

    def get_artist_by_name(self, name: str) -> Optional[dict]:
        aid = self._data["indexes"]["by_name"].get(name)
        return self._data["artists"].get(aid) if aid else None

    def get_artist_by_slug(self, slug: str) -> Optional[dict]:
        aid = self._data["indexes"]["by_slug"].get(slug)
        return self._data["artists"].get(aid) if aid else None

    def get_collaborations(self, name: str) -> list[dict]:
        artist = self.get_artist_by_name(name)
        return artist.get("collaborations", []) if artist else []

    def get_recommended(self, name: str) -> list[dict]:
        artist = self.get_artist_by_name(name)
        return artist.get("recommended_collaborations", []) if artist else []

    def get_artists_by_genre(self, genre: str) -> list[dict]:
        aids = self._data["indexes"]["by_genre"].get(genre, [])
        return [self._data["artists"][aid] for aid in aids if aid in self._data["artists"]]

    def get_artists_by_vocal_type(self, vtype: str) -> list[dict]:
        aids = self._data["indexes"]["by_vocal_type"].get(vtype, [])
        return [self._data["artists"][aid] for aid in aids if aid in self._data["artists"]]

    def get_artists_by_era(self, era: str) -> list[dict]:
        aids = self._data["indexes"]["by_era"].get(era, [])
        return [self._data["artists"][aid] for aid in aids if aid in self._data["artists"]]

    def search(self, query: str) -> list[dict]:
        query = query.lower()
        results = []
        for artist in self._data["artists"].values():
            if query in artist["name"].lower():
                results.append(artist)
                continue
            for collab in artist.get("collaborations", []):
                if query in collab.get("with_artist_name", "").lower():
                    results.append(artist)
                    break
            else:
                for tag in artist.get("tags", []):
                    if query in tag.lower():
                        results.append(artist)
                        break
        return results

    def find_by_similar_prosody(self, profile: dict, top_k: int = 5) -> list[dict]:
        if not profile:
            return []
        candidates = []
        for artist in self._data["artists"].values():
            ap = artist.get("prosody_profile", {})
            if not ap:
                continue
            score = 0
            if profile.get("mean_pitch_hz") and ap.get("mean_pitch_hz"):
                diff = abs(profile["mean_pitch_hz"] - ap["mean_pitch_hz"])
                score = max(0, 1 - diff / 200)
            if ap.get("timbre_descriptors") and profile.get("timbre_descriptors"):
                overlap = set(ap["timbre_descriptors"]) & set(profile["timbre_descriptors"])
                score += len(overlap) * 0.1
            candidates.append((score, artist))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:top_k]]

    def add_artist(self, artist: dict) -> str:
        aid = artist.get("id") or str(hash(artist["name"]))[:8]
        slug = artist.get("slug", artist["name"].lower().replace(" ", "-"))
        artist["id"] = aid
        artist["slug"] = slug
        self._data["artists"][aid] = artist
        self._data["indexes"]["by_name"][artist["name"]] = aid
        self._data["indexes"]["by_slug"][slug] = aid
        for genre in artist.get("metadata", {}).get("genres", []):
            self._data["indexes"]["by_genre"].setdefault(genre, []).append(aid)
        vt = artist.get("metadata", {}).get("vocal_type", "unknown")
        self._data["indexes"]["by_vocal_type"].setdefault(vt, []).append(aid)
        era = artist.get("metadata", {}).get("era", "unknown")
        self._data["indexes"]["by_era"].setdefault(era, []).append(aid)
        self._data["artist_count"] = len(self._data["artists"])
        return aid

    def remove_artist(self, name_or_id: str) -> bool:
        artist = self.get_artist_by_name(name_or_id) or self.get_artist(name_or_id)
        if not artist:
            return False
        aid = artist["id"]
        del self._data["artists"][aid]
        for index_key in ("by_name", "by_slug"):
            for key, val in list(self._data["indexes"].get(index_key, {}).items()):
                if val == aid:
                    del self._data["indexes"][index_key][key]
        for index_key in ("by_genre", "by_vocal_type", "by_era"):
            for genre, aids in self._data["indexes"].get(index_key, {}).items():
                if aid in aids:
                    aids.remove(aid)
        self._data["artist_count"] = len(self._data["artists"])
        return True

    def get_prosody_for_tts(self, artist_name: str) -> dict:
        artist = self.get_artist_by_name(artist_name)
        if not artist:
            return {}
        return {
            "mean_pitch_hz": artist.get("prosody_profile", {}).get("mean_pitch_hz"),
            "vocal_range": artist.get("metadata", {}).get("vocal_range", "unknown"),
            "style_descriptors": artist.get("prosody_profile", {}).get("style_descriptors", []),
        }

    def get_bpm_for_beat_reproducer(self, artist_name: str) -> Optional[dict]:
        artist = self.get_artist_by_name(artist_name)
        if not artist:
            return None
        bpm_range = artist.get("metadata", {}).get("bpm_range", {})
        return {
            "min": bpm_range.get("min"),
            "max": bpm_range.get("max"),
            "typical": bpm_range.get("typical"),
            "genres": artist.get("metadata", {}).get("genres", []),
        }
