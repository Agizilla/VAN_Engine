import difflib
import functools
from pathlib import Path
from typing import Any

from .base import BaseSkill, register_skill

_STUB_LEXICON: dict = {
    "artists": [],
    "collaborations": [],
}


def _import_lexicon():
    try:
        from lexicon.music_lexicon import MusicLexicon
        return MusicLexicon()
    except ImportError:
        return None


def _make_stub() -> dict:
    return dict(_STUB_LEXICON)


class _LexiconWrapper:
    def __init__(self, lex):
        self._lex = lex

    def get_known_keys(self) -> list[str]:
        try:
            return list(self._lex.artists_by_name.keys()) if hasattr(self._lex, "artists_by_name") else []
        except Exception:
            return []

    @functools.lru_cache(maxsize=256)
    def search(self, query: str) -> list:
        return self._lex.search(query)

    def get_artist_by_name(self, name: str):
        return self._lex.get_artist_by_name(name)

    def get_collaborations(self, name: str):
        return self._lex.get_collaborations(name)

    def get_recommended(self, name: str):
        return self._lex.get_recommended(name)

    def get_artists_by_genre(self, genre: str):
        return self._lex.get_artists_by_genre(genre)

    @property
    def count(self):
        return self._lex.count


@register_skill("lexicon", "data")
class LexiconSkill(BaseSkill):
    name = "lexicon"
    description = "Query the music artist lexicon - search artists, collabs, genres"
    category = "data"
    required_libs = []

    def execute(self, **kwargs: Any) -> dict:
        action = kwargs.get("action", "search")
        query = kwargs.get("query", "")
        name = kwargs.get("name", "")

        raw_lex = _import_lexicon()
        if raw_lex is None:
            raw_lex = _make_stub()

        lex = _LexiconWrapper(raw_lex)

        try:
            if action == "search":
                if not query:
                    return {"error": "No search query", "result": None}
                results = lex.search(query)
                return {"error": None, "result": {
                    "count": len(results),
                    "artists": [{"name": a["name"], "id": a["id"], "collab_count": len(a.get("collaborations", []))} for a in results],
                }}

            elif action == "artist":
                if not name:
                    return {"error": "No artist name", "result": None}
                artist = lex.get_artist_by_name(name)
                if not artist:
                    known = lex.get_known_keys()
                    if known:
                        matches = difflib.get_close_matches(name, known, n=3, cutoff=0.5)
                        if matches:
                            return {"error": None, "result": {
                                "suggestions": matches,
                                "message": f"Artist not found: {name}. Did you mean: {', '.join(matches)}?",
                            }}
                    return {"error": f"Artist not found: {name}", "result": None}
                collabs = len(lex.get_collaborations(name))
                recommended = len(lex.get_recommended(name))
                return {"error": None, "result": {
                    "name": artist["name"],
                    "collaborations": collabs,
                    "recommended": recommended,
                    "genres": artist.get("metadata", {}).get("genres", []),
                    "tags": artist.get("tags", []),
                }}

            elif action == "collabs":
                if not name:
                    return {"error": "No artist name", "result": None}
                collabs = lex.get_collaborations(name)
                song_titles = []
                for c in collabs:
                    for s in c.get("songs", []):
                        song_titles.append({
                            "with": c.get("with_artist_name", "unknown"),
                            "song": s["title"],
                        })
                return {"error": None, "result": {
                    "artist": name,
                    "count": len(song_titles),
                    "songs": song_titles,
                }}

            elif action == "genre":
                genre = query or kwargs.get("genre", "hip-hop")
                artists = lex.get_artists_by_genre(genre)
                return {"error": None, "result": {
                    "genre": genre,
                    "count": len(artists),
                    "artists": [a["name"] for a in artists],
                }}

            elif action == "count":
                return {"error": None, "result": {"count": lex.count}}

            return {"error": f"Unknown action: {action}", "result": None}

        except Exception as e:
            return {"error": str(e), "result": None}
