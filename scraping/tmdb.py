# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any, Optional
from requests_cache import CachedSession

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_AVAILABLE = bool(TMDB_API_KEY)

# cache 24h
session = CachedSession(
    cache_name=".tmdb_cache",
    backend="sqlite",
    expire_after=60 * 60 * 24,
)
session.headers.update({"Accept": "application/json"})

BASE = "https://api.themoviedb.org/3"
IMG_W = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"

def _get(path: str, params: Optional[Dict[str, Any]] = None):
    p = {"api_key": TMDB_API_KEY, "language": "pt-BR"}
    if params:
        p.update(params)
    r = session.get(f"{BASE}{path}", params=p, timeout=20)
    r.raise_for_status()
    return r.json()

def _map_results(results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    out = []
    for i, m in enumerate(results[:limit], start=1):
        out.append(
            {
                "title": m.get("title") or m.get("name"),
                "year": (m.get("release_date", "") or "").split("-")[0] or None,
                "rank": i,
                "rating": m.get("vote_average"),
                "url": f"https://www.themoviedb.org/movie/{m.get('id')}",
                "poster": f"{IMG_W}{m.get('poster_path')}" if m.get("poster_path") else None,
                "backdrop": f"{IMG_ORIG}{m.get('backdrop_path')}" if m.get("backdrop_path") else None,
                "overview": m.get("overview"),
                "source": "tmdb",
                "tmdb_id": m.get("id"),
            }
        )
    return out

def fetch_tmdb_list(category: str = "trending", limit: int = 20) -> List[Dict[str, Any]]:
    if not TMDB_AVAILABLE:
        return []
    if category == "trending":
        data = _get("/trending/movie/day")
    elif category == "top_rated":
        data = _get("/movie/top_rated")
    elif category == "now_playing":
        data = _get("/movie/now_playing")
    else:
        data = _get("/trending/movie/week")
    return _map_results(data.get("results", []), limit)

def fetch_tmdb_overview(title: str, year: str | None = None) -> str | None:
    if not TMDB_AVAILABLE:
        return None
    try:
        params = {"query": title}
        if year:
            params["year"] = year
        data = _get("/search/movie", params=params)
        results = data.get("results", [])
        if not results:
            return None
        return results[0].get("overview")
    except Exception:
        return None

def search_tmdb_movies(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not TMDB_AVAILABLE or not query:
        return []
    data = _get("/search/movie", params={"query": query, "include_adult": False})
    return _map_results(data.get("results", []), limit)

def fetch_tmdb_trailer_key(tmdb_id: int | None) -> str | None:
    if not (TMDB_AVAILABLE and tmdb_id):
        return None
    try:
        data = _get(f"/movie/{tmdb_id}/videos")
        for v in data.get("results", []):
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
                return v.get("key")
    except Exception:
        return None
    return None
