# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, render_template, request
from scraping import fetch_imdb_list, fetch_tmdb_list, TMDB_AVAILABLE
from scraping.tmdb import fetch_tmdb_overview  # novo helper
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Categorias com ícones
CATEGORIES = [
    {"value": "most_popular", "label": "🔥 Mais Populares"},
    {"value": "top_rated", "label": "⭐ Top 25"},
    {"value": "in_theaters", "label": "🎬 Em Cartaz"},
]

if TMDB_AVAILABLE:
    CATEGORIES.extend(
        [
            {"value": "tmdb_trending", "label": "⚡ Trending (dia)"},
            {"value": "tmdb_top_rated", "label": "🏆 Top Rated"},
            {"value": "tmdb_now_playing", "label": "🎟️ Em Cartaz (TMDb)"},
        ]
    )


def enrich_with_tmdb(movies):
    """Tenta preencher sinopses para filmes do IMDb usando TMDb."""
    enriched = []
    for m in movies:
        if not m.get("overview"):  # só se não tiver sinopse
            overview = fetch_tmdb_overview(m["title"], m.get("year"))
            if overview:
                m["overview"] = overview
        enriched.append(m)
    return enriched


def get_movies(source_key: str, limit: int = 20):
    try:
        if source_key == "most_popular":
            movies = fetch_imdb_list("most_popular", limit)
            return enrich_with_tmdb(movies)
        if source_key == "top_rated":
            movies = fetch_imdb_list("top_rated", limit)
            return enrich_with_tmdb(movies)
        if source_key == "in_theaters":
            movies = fetch_imdb_list("in_theaters", limit)
            if (not movies or len(movies) == 0) and TMDB_AVAILABLE:
                movies = fetch_tmdb_list("now_playing", limit)
            else:
                movies = enrich_with_tmdb(movies)
            return movies
        if source_key == "tmdb_trending":
            return fetch_tmdb_list("trending", limit)
        if source_key == "tmdb_top_rated":
            return fetch_tmdb_list("top_rated", limit)
        if source_key == "tmdb_now_playing":
            return fetch_tmdb_list("now_playing", limit)
    except Exception as e:
        print(f"[ERRO] Falha ao buscar filmes: {e}")
    return []


@app.route("/", methods=["GET", "POST"])
def index():
    source = request.form.get("source") or "most_popular"
    limit = int(request.form.get("limit") or 20)
    query = (request.form.get("query") or "").strip().lower()

    movies = get_movies(source, limit)

    if query:
        movies = [m for m in movies if query in (m.get("title", "").lower())]

    return render_template(
        "index.html",
        movies=movies,
        categories=CATEGORIES,
        selected=source,
        limit=limit,
        query=query,
        now=datetime.now(),
        tmdb_enabled=TMDB_AVAILABLE,
    )


if __name__ == "__main__":
    app.run(debug=True)
