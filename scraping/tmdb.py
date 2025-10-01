# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any
import requests
from requests_cache import CachedSession

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_AVAILABLE = bool(TMDB_API_KEY)

# Sessão com cache de 24h
session = CachedSession(
    cache_name=".tmdb_cache",
    backend="sqlite",
    expire_after=60 * 60 * 24,  # 🔥 24 horas
)
session.headers.update({"Accept": "application/json"})

BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"  # alta qualidade


def _get(path: str, params: Dict[str, Any] | None = None):
    p = {"api_key": TMDB_API_KEY, "language": "pt-BR"}
    if params:
        p.update(params)
    r = session.get(f"{BASE}{path}", params=p, timeout=20)
    r.raise_for_status()
    return r.json()


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

    out = []
    for i, m in enumerate(data.get("results", [])[:limit], start=1):
        out.append(
            {
                "title": m.get("title") or m.get("name"),
                "year": (m.get("release_date", "") or "").split("-")[0] or None,
                "rank": i,
                "rating": m.get("vote_average"),
                "url": f"https://www.themoviedb.org/movie/{m.get('id')}",
                "poster": f"{IMG}{m.get('poster_path')}" if m.get("poster_path") else None,
                "overview": m.get("overview"),
                "source": "tmdb",
            }
        )
    return out


def fetch_tmdb_overview(title: str, year: str | None = None) -> str | None:
    """Busca a sinopse de um filme no TMDb pelo título/ano."""
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
