# -*- coding: utf-8 -*-
from datetime import datetime
import os
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from scraping import fetch_imdb_list, fetch_tmdb_list, TMDB_AVAILABLE
from scraping.tmdb import (
    fetch_tmdb_overview,
    search_tmdb_movies,
    fetch_tmdb_trailer_key,
)

load_dotenv()

app = Flask(__name__)

# ----------------------------
# Timezone
# ----------------------------
# Permite configurar via .env (APP_TIMEZONE=America/Sao_Paulo, Europe/Lisbon, etc.)
APP_TZ_NAME = os.getenv("APP_TIMEZONE", "America/Sao_Paulo")

try:
    APP_TZ = ZoneInfo(APP_TZ_NAME)
except Exception:
    # fallback seguro caso o nome do fuso esteja inválido
    APP_TZ = ZoneInfo("UTC")

def now_local() -> datetime:
    """Retorna datetime c/ timezone no fuso configurado."""
    return datetime.now(APP_TZ)

# Categorias limpas + ícones
CATEGORIES = [
    {"value": "most_popular", "label": "🔥 Mais Populares"},
    {"value": "top_rated", "label": "⭐ Top 250"},
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
    """Completa sinopse para itens do IMDb consultando o TMDb por título/ano."""
    if not TMDB_AVAILABLE:
        return movies
    out = []
    for m in movies:
        if not m.get("overview"):
            overview = fetch_tmdb_overview(m.get("title"), m.get("year"))
            if overview:
                m["overview"] = overview
        out.append(m)
    return out

def get_movies(source_key: str, limit: int = 20):
    try:
        if source_key == "most_popular":
            return enrich_with_tmdb(fetch_imdb_list("most_popular", limit))
        if source_key == "top_rated":
            return enrich_with_tmdb(fetch_imdb_list("top_rated", limit))
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
        mode="lists",
        movies=movies,
        categories=CATEGORIES,
        selected=source,
        limit=limit,
        query=query,
        now=now_local(),                # <<< timezone-aware
        tmdb_enabled=TMDB_AVAILABLE,
    )

@app.route("/search")
def search():
    """Busca livre no TMDb (por título)."""
    q = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit") or 20)
    if not q:
        return render_template(
            "index.html",
            mode="lists",
            movies=get_movies("most_popular", limit),
            categories=CATEGORIES,
            selected="most_popular",
            limit=limit,
            query="",
            now=now_local(),            # <<< timezone-aware
            tmdb_enabled=TMDB_AVAILABLE,
        )
    movies = search_tmdb_movies(q, limit)
    return render_template(
        "index.html",
        mode="search",
        movies=movies,
        categories=CATEGORIES,
        selected="tmdb_search",
        limit=limit,
        query=q,
        now=now_local(),                # <<< timezone-aware
        tmdb_enabled=TMDB_AVAILABLE,
        search_term=q,
    )

@app.route("/api/trailer")
def api_trailer():
    """Retorna a URL do trailer do YouTube a partir de um TMDb ID."""
    tmdb_id = request.args.get("tmdb_id", type=int)
    key = fetch_tmdb_trailer_key(tmdb_id)
    if not key:
        return jsonify({"ok": False, "url": None}), 200
    return jsonify({"ok": True, "url": f"https://www.youtube.com/watch?v={key}"}), 200

if __name__ == "__main__":
    app.run(debug=True)
