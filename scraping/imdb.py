# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass
from typing import List, Literal, Dict, Any
import requests
from bs4 import BeautifulSoup
from requests_cache import CachedSession

# Sessão com cache de 24h
session = CachedSession(
    cache_name=".imdb_cache",
    backend="sqlite",
    expire_after=60 * 60 * 24,  # 🔥 24 horas
)
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
)


@dataclass
class Movie:
    title: str
    year: str | None
    rank: int | None
    rating: float | None
    url: str | None
    poster: str | None


IMDbCategory = Literal[
    "most_popular",
    "top_rated",
    "in_theaters",
]

IMDB_URLS = {
    "most_popular": "https://www.imdb.com/chart/moviemeter/",
    "top_rated": "https://www.imdb.com/chart/top/",
    "in_theaters": "https://www.imdb.com/movies-in-theaters/",
}


def _abs(url: str) -> str:
    if url.startswith("http"):
        return url
    return f"https://www.imdb.com{url}"


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"\s+", " ", text).strip()


def _upgrade_poster(url: str | None) -> str | None:
    """Tenta melhorar a resolução do poster do IMDb."""
    if not url:
        return None
    if "._V1_" in url:
        base = url.split("._V1_")[0]
        return f"{base}._V1_FMjpg_UX600_.jpg"
    return url


def fetch_imdb_list(category: IMDbCategory = "most_popular", limit: int = 20) -> List[Dict[str, Any]]:
    url = IMDB_URLS[category]
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    movies: List[Movie] = []

    if category in ("most_popular", "top_rated"):
        rows = soup.select('[data-testid="chart-layout-main-column"] a.ipc-title-link-wrapper')
        if not rows:
            rows = soup.select("table tbody tr")

        rank = 0
        for row in rows:
            try:
                if row.name == "a":
                    title_el = row.select_one('[data-testid="title"]') or row
                    title = _clean(title_el.get_text())
                    href = row.get("href")
                    url_full = _abs(href) if href else None
                    poster_el = row.find_previous("img") or row.find_next("img")
                    poster = _upgrade_poster(poster_el.get("src")) if poster_el else None
                    year = None
                    rating = None
                else:
                    title_el = row.select_one("td.titleColumn a")
                    title = _clean(title_el.get_text()) if title_el else None
                    href = title_el.get("href") if title_el else None
                    url_full = _abs(href) if href else None
                    year_el = row.select_one("span.secondaryInfo")
                    year = _clean(year_el.get_text(" ").strip("()")) if year_el else None
                    rating_el = row.select_one("td.imdbRating strong")
                    rating = float(rating_el.get_text()) if rating_el and rating_el.get_text().strip() else None
                    poster_el = row.select_one("td.posterColumn img")
                    poster = _upgrade_poster(poster_el.get("src")) if poster_el else None

                rank += 1
                if not title:
                    continue

                movies.append(
                    Movie(
                        title=title,
                        year=year,
                        rank=rank,
                        rating=rating,
                        url=url_full,
                        poster=poster,
                    )
                )
                if len(movies) >= limit:
                    break
            except Exception:
                continue

    elif category == "in_theaters":
        cards = soup.select('[data-testid="list-page-movie-card"]')
        for idx, c in enumerate(cards, start=1):
            title_el = c.select_one('[data-testid="title"]')
            title = _clean(title_el.get_text()) if title_el else None
            year = None
            rating = None
            link_el = c.select_one('a.ipc-lockup-overlay, a[href*="/title/"]')
            url_full = _abs(link_el.get("href")) if link_el else None
            poster_el = c.select_one("img")
            poster = _upgrade_poster(poster_el.get("src")) if poster_el else None
            if not title:
                continue
            movies.append(Movie(title=title, year=year, rank=idx, rating=rating, url=url_full, poster=poster))
            if len(movies) >= limit:
                break

    out = [
        {
            "title": m.title,
            "year": m.year,
            "rank": m.rank,
            "rating": m.rating,
            "url": m.url,
            "poster": m.poster,
            "source": "imdb",
        }
        for m in movies
    ]
    return out
