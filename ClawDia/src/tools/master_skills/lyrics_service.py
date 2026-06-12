"""
LyricsService — Genius API integration for Clawdia.

Extracted from ClaudeHipHopperList enrich_data.py.
Provides song search, lyrics fetching, annotation extraction,
and batch enrichment of audio metadata.

Usage:
    svc = LyricsService(access_token="your_genius_token")
    hits = svc.search_song("Never Gonna Give You Up")
    lyrics = svc.get_lyrics(hits[0]["id"])
"""

import os
import re
import json
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote_plus

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Genius API helpers  (no extra dependency — pure stdlib)
# ---------------------------------------------------------------------------

GENIUS_API_BASE = "https://api.genius.com"
GENIUS_EMBED_BASE = "https://genius.com/songs/{id}/embed"

_SEARCH_CACHE: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 3600


def _genius_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _json_get(url: str, headers: dict, timeout: int = 30) -> dict | None:
    import urllib.request as ureq
    import urllib.error as uerr
    req = ureq.Request(url, headers=headers)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with ureq.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except uerr.HTTPError as e:
            if e.code == 429:
                wait = min(60, (2 ** attempt) + random.random())
                log.warning("Rate limited (429). Retrying in %.2fs...", wait)
                time.sleep(wait)
                continue
            log.warning("HTTP %d for %s", e.code, url)
            return None
        except Exception as e:
            log.warning("GET %s failed: %s", url, e)
            return None
    log.warning("Max retries exhausted for %s", url)
    return None


def _scrape_lyrics(song_id: int, timeout: int = 30) -> str | None:
    """Scrape lyrics from the Genius embed page (no API scope needed)."""
    import urllib.request as ureq
    import urllib.error as uerr
    url = GENIUS_EMBED_BASE.format(id=song_id)
    req = ureq.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with ureq.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode("utf-8")
                break
        except uerr.HTTPError as e:
            if e.code == 429:
                wait = min(60, (2 ** attempt) + random.random())
                log.warning("Rate limited (429). Retrying in %.2fs...", wait)
                time.sleep(wait)
                continue
            log.warning("Embed fetch HTTP %d for song %d", e.code, song_id)
            return None
        except Exception as e:
            log.warning("Embed fetch failed for song %d: %s", song_id, e)
            return None
    if html is None:
        return None

    # Try multiple DOM structures
    m = re.search(r'<div[^>]+data-lyrics-container[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        m = re.search(r'<div class="lyrics\s?"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        # Fallback: extract from window.__INITIAL_STATE__ JSON
        m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if m:
            try:
                state = json.loads(m.group(1))
                lyrics_data = state.get("songPage", {}).get("lyricsData", {})
                if lyrics_data:
                    raw = lyrics_data
                    if isinstance(raw, dict):
                        raw = raw.get("lyrics", {}).get("plain", "")
                    raw = re.sub(r'<[^>]+>', '', raw)
                    return raw.strip()
            except (json.JSONDecodeError, AttributeError):
                pass
    if not m:
        log.info("No lyrics container found for song %d", song_id)
        return None

    raw = m.group(1)
    raw = re.sub(r'<br\s*/?>', '\n', raw)
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = html.unescape(raw) if hasattr(html, 'unescape') else raw
    return raw.strip()


# ---------------------------------------------------------------------------
#  LyricsService
# ---------------------------------------------------------------------------

class LyricsService:
    """Fetch song metadata and lyrics from Genius."""

    def __init__(self, access_token: str | None = None, timeout: int = 30):
        self.token = access_token or os.environ.get("GENIUS_ACCESS_TOKEN", "")
        self.timeout = timeout
        if not self.token or self.token == "your_token_here":
            raise ValueError(
                "Genius access token is required. Set the GENIUS_ACCESS_TOKEN "
                "environment variable or pass it to LyricsService(access_token=...). "
                "Get a token at: https://genius.com/api-clients"
            )
        self._validate_token()

    def _validate_token(self):
        """Validate the token with a lightweight API call."""
        url = f"{GENIUS_API_BASE}/search?q=test&per_page=1"
        data = _json_get(url, _genius_headers(self.token), timeout=self.timeout)
        if data is None:
            log.warning("Genius token validation failed — check your token")

    # ── search ──────────────────────────────────────────────────────────

    def search_song(self, query: str, per_page: int = 10,
                    timeout: int | None = None) -> list[dict]:
        """Search Genius for a song. Returns list of hit dicts."""
        t = timeout or self.timeout
        now = time.time()
        cache_key = f"search:{query}:{per_page}"
        if cache_key in _SEARCH_CACHE:
            ts, cached = _SEARCH_CACHE[cache_key]
            if now - ts < _CACHE_TTL:
                return cached
        url = f"{GENIUS_API_BASE}/search?q={quote_plus(query)}&per_page={per_page}"
        data = _json_get(url, _genius_headers(self.token), timeout=t)
        if not data:
            return []
        hits = []
        for hit in (data.get("response", {}).get("hits", [])):
            result = hit.get("result", {})
            hits.append({
                "id": result.get("id"),
                "title": result.get("title"),
                "artist": result.get("primary_artist", {}).get("name"),
                "url": result.get("url"),
                "album": result.get("album", {}).get("name") if result.get("album") else None,
                "release_date": result.get("release_date_for_display"),
                "image": result.get("header_image_thumbnail_url"),
                "instrumental": result.get("instrumental", False),
            })
        _SEARCH_CACHE[cache_key] = (time.time(), hits)
        return hits

    def search_artist(self, artist_name: str, per_page: int = 20,
                      timeout: int | None = None) -> list[dict]:
        """Search for an artist. Returns list of artist dicts."""
        t = timeout or self.timeout
        url = f"{GENIUS_API_BASE}/search?q={quote_plus(artist_name)}&type=artist&per_page={per_page}"
        data = _json_get(url, _genius_headers(self.token), timeout=t)
        if not data:
            return []
        return [
            {
                "id": h.get("result", {}).get("id"),
                "name": h.get("result", {}).get("name"),
                "image": h.get("result", {}).get("image_url"),
            }
            for h in data.get("response", {}).get("hits", [])
            if h.get("type") == "artist"
        ]

    # ── lyrics ──────────────────────────────────────────────────────────

    def get_lyrics(self, song_id: int, timeout: int | None = None) -> str | None:
        """Fetch lyrics for a song by Genius song ID."""
        t = timeout or self.timeout
        return _scrape_lyrics(song_id, timeout=t)

    def get_lyrics_by_title(self, title: str, artist: str = "",
                            timeout: int | None = None) -> str | None:
        """Search then fetch lyrics for best-matching song."""
        q = f"{title} {artist}".strip()
        hits = self.search_song(q, timeout=timeout)
        if not hits:
            return None
        # Prefer exact title match
        for h in hits:
            if h["title"] and h["title"].lower() == title.lower():
                return self.get_lyrics(h["id"], timeout=timeout)
        return self.get_lyrics(hits[0]["id"], timeout=timeout)

    # ── annotations ─────────────────────────────────────────────────────

    def get_song_annotations(self, song_id: int, timeout: int | None = None) -> list[dict]:
        """Fetch referents (annotations) for a song."""
        t = timeout or self.timeout
        url = f"{GENIUS_API_BASE}/referents?song_id={song_id}&per_page=25"
        data = _json_get(url, _genius_headers(self.token), timeout=t)
        if not data:
            return []
        annotations = []
        for ref in data.get("response", {}).get("referents", []):
            ann = ref.get("annotations", [{}])[0] if ref.get("annotations") else {}
            annotations.append({
                "fragment": ref.get("fragment", ""),
                "body": ann.get("body", {}).get("plain", ""),
                "votes": ann.get("vote_count"),
            })
        return annotations

    # ── song detail ─────────────────────────────────────────────────────

    def get_song_detail(self, song_id: int, timeout: int | None = None) -> dict | None:
        """Full song metadata from Genius API."""
        t = timeout or self.timeout
        url = f"{GENIUS_API_BASE}/songs/{song_id}?text_format=plain"
        data = _json_get(url, _genius_headers(self.token), timeout=t)
        if not data:
            return None
        s = data.get("response", {}).get("song", {})
        return {
            "id": s.get("id"),
            "title": s.get("title"),
            "artist": s.get("primary_artist", {}).get("name"),
            "album": s.get("album", {}).get("name") if s.get("album") else None,
            "release_date": s.get("release_date_for_display"),
            "url": s.get("url"),
            "image": s.get("header_image_thumbnail_url"),
            "lyrics_state": s.get("lyrics_state"),
            "producer_artists": [a.get("name") for a in s.get("producer_artists", [])],
            "writer_artists": [a.get("name") for a in s.get("writer_artists", [])],
            "annotation_count": s.get("annotation_count"),
            "lyrics": self.get_lyrics(song_id, timeout=t),
        }

    # ── batch / enrichment ──────────────────────────────────────────────

    def enrich_metadata(self, title: str, artist: str = "",
                        timeout: int | None = None) -> dict:
        """One-shot: search + detail + lyrics, returns flat dict suitable for merging."""
        t = timeout or self.timeout
        hits = self.search_song(f"{title} {artist}".strip(), timeout=t)
        if not hits:
            return {"title": title, "artist": artist}
        best = hits[0]
        detail = self.get_song_detail(best["id"], timeout=t) or {}
        lyrics = self.get_lyrics(best["id"], timeout=t)
        return {
            "title": detail.get("title") or best.get("title") or title,
            "artist": detail.get("artist") or best.get("artist") or artist,
            "album": detail.get("album"),
            "release_date": detail.get("release_date"),
            "genius_url": detail.get("url") or best.get("url"),
            "image": detail.get("image") or best.get("image"),
            "lyrics": lyrics or "",
            "annotation_count": detail.get("annotation_count"),
            "producers": detail.get("producer_artists", []),
            "writers": detail.get("writer_artists", []),
        }

    def batch_enrich(self, songs: list[dict], delay_s: float = 0.5,
                     progress_callback: Callable[[int, int], None] | None = None,
                     timeout: int | None = None) -> list[dict]:
        """Enrich a list of {title, artist} dicts with Genius metadata."""
        t = timeout or self.timeout
        results = []
        for i, song in enumerate(songs):
            if progress_callback:
                progress_callback(i + 1, len(songs))
            try:
                enriched = self.enrich_metadata(song.get("title", ""), song.get("artist", ""), timeout=t)
                results.append(enriched)
            except Exception as e:
                log.error("Failed to enrich %s: %s", song.get("title"), e)
                results.append({**song, "lyrics": "", "error": str(e)})
            time.sleep(delay_s)
        return results

    def artist_top_songs(self, artist_id: int, per_page: int = 20,
                         timeout: int | None = None) -> list[dict]:
        """Get top songs for an artist by Genius artist ID."""
        t = timeout or self.timeout
        url = f"{GENIUS_API_BASE}/artists/{artist_id}/songs?per_page={per_page}&sort=popularity"
        data = _json_get(url, _genius_headers(self.token), timeout=t)
        if not data:
            return []
        return [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "url": s.get("url"),
                "popularity": s.get("popularity"),
            }
            for s in data.get("response", {}).get("songs", [])
        ]

    def find_artist_id(self, artist_name: str, timeout: int | None = None) -> int | None:
        """Resolve an artist name to a Genius artist ID."""
        artists = self.search_artist(artist_name, timeout=timeout)
        for a in artists:
            if a["name"] and a["name"].lower() == artist_name.lower():
                return a["id"]
        return artists[0]["id"] if artists else None

    # ── async / non-blocking ───────────────────────────────────────────

    async def search_song_async(self, query: str, per_page: int = 10,
                                timeout: int | None = None) -> list[dict]:
        """Async search for a song (runs sync version in thread executor)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.search_song, query, per_page, timeout
        )

    async def get_lyrics_async(self, url_or_id: str | int, timeout: int | None = None) -> str | None:
        """Async lyrics fetch. Accepts a Genius song URL or ID."""
        t = timeout or self.timeout
        if isinstance(url_or_id, int) or (isinstance(url_or_id, str) and url_or_id.isdigit()):
            song_id = int(url_or_id)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.get_lyrics, song_id, t)
        import urllib.request as ureq
        loop = asyncio.get_event_loop()
        def _fetch():
            req = ureq.Request(url_or_id, headers={"User-Agent": "Mozilla/5.0"})
            with ureq.urlopen(req, timeout=t) as resp:
                return resp.read().decode("utf-8")
        try:
            html = await loop.run_in_executor(None, _fetch)
        except Exception as e:
            log.warning("Async embed fetch failed for %s: %s", url_or_id, e)
            return None
        return _extract_lyrics_from_html(html) if html else None

    async def batch_enrich_async(self, songs: list[dict], delay_s: float = 0.5,
                                 progress_callback: Callable[[int, int], None] | None = None,
                                 timeout: int | None = None) -> list[dict]:
        """Async batch enrichment."""
        loop = asyncio.get_event_loop()
        results = []
        for i, song in enumerate(songs):
            if progress_callback:
                await loop.run_in_executor(None, progress_callback, i + 1, len(songs))
            try:
                enriched = await loop.run_in_executor(
                    None, self.enrich_metadata,
                    song.get("title", ""), song.get("artist", ""), timeout
                )
                results.append(enriched)
            except Exception as e:
                log.error("Failed to enrich %s: %s", song.get("title"), e)
                results.append({**song, "lyrics": "", "error": str(e)})
            await asyncio.sleep(delay_s)
        return results

    def get_capabilities(self) -> list[str]:
        return [
            "song_search",
            "lyrics_fetch",
            "annotation_extraction",
            "song_detail",
            "batch_enrichment",
            "artist_lookup",
            "async_search",
            "async_lyrics",
            "async_batch",
        ]


def _extract_lyrics_from_html(html: str) -> str | None:
    """Extract lyrics text from Genius embed HTML."""
    m = re.search(r'<div[^>]+data-lyrics-container[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        m = re.search(r'<div class="lyrics\s?"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if m:
            try:
                state = json.loads(m.group(1))
                lyrics_data = state.get("songPage", {}).get("lyricsData", {})
                if lyrics_data:
                    raw = lyrics_data
                    if isinstance(raw, dict):
                        raw = raw.get("lyrics", {}).get("plain", "")
                    raw = re.sub(r'<[^>]+>', '', raw)
                    return raw.strip()
            except (json.JSONDecodeError, AttributeError):
                pass
        return None
    raw = m.group(1)
    raw = re.sub(r'<br\s*/?>', '\n', raw)
    raw = re.sub(r'<[^>]+>', '', raw)
    raw = html.unescape(raw) if hasattr(html, 'unescape') else raw
    return raw.strip()
