// ========== THEME ==========
(function () {
  const body = document.body;
  const stored = localStorage.getItem('theme');
  if (stored) body.setAttribute('data-theme', stored);
  const btn = document.getElementById('themeToggle');
  if (btn) {
    const setIcon = () => btn.textContent = body.getAttribute('data-theme') === 'dark' ? '🌙' : '☀️';
    setIcon();
    btn.addEventListener('click', () => {
      const next = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      body.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      setIcon();
    });
  }
})();

// ========== FAVORITOS ==========
const FAV_KEY = 'movie_favs_v1';
const getFavs = () => { try { return JSON.parse(localStorage.getItem(FAV_KEY) || '[]'); } catch { return []; } };
const saveFavs = (arr) => localStorage.setItem(FAV_KEY, JSON.stringify(arr));
const isFav = (id) => getFavs().includes(id);
const toggleFav = (id) => { const f = getFavs(); const i = f.indexOf(id); i >= 0 ? f.splice(i, 1) : f.push(id); saveFavs(f); return f.includes(id); };

function syncFavButtons() {
  document.querySelectorAll('.card').forEach(card => {
    const id = card.dataset.id;
    const btn = card.querySelector('.fav-btn');
    if (!btn) return;
    btn.classList.toggle('active', isFav(id));
  });
}
document.addEventListener('click', e => {
  const btn = e.target.closest('.fav-btn');
  if (!btn) return;
  const card = e.target.closest('.card');
  const id = card.dataset.id;
  const active = toggleFav(id);
  btn.classList.toggle('active', active);
  const modalBtn = document.getElementById('modalFavBtn');
  if (modalBtn && modalBtn.dataset.id === id) modalBtn.classList.toggle('active', active);
});
document.getElementById('toggleFavs')?.addEventListener('click', () => {
  const onlyFavs = !document.body.classList.contains('show-favs');
  document.body.classList.toggle('show-favs', onlyFavs);
  const favSet = new Set(getFavs());
  document.querySelectorAll('#cardsGrid .card').forEach(card => {
    card.style.display = (!onlyFavs || favSet.has(card.dataset.id)) ? '' : 'none';
  });
});

// ========== MODAL + TRAILER ==========
const modal = document.getElementById('movieModal');
const mClose = modal?.querySelector('.modal-close');
const mPoster = modal?.querySelector('.modal-poster');
const mTitle = modal?.querySelector('.modal-title');
const mMeta = modal?.querySelector('.modal-meta');
const mOverview = modal?.querySelector('.modal-overview');
const mDetails = document.getElementById('modalDetails');
const mTrailer = document.getElementById('modalTrailer');
const mFavBtn = document.getElementById('modalFavBtn');

function openModalFromCard(card) {
  const data = card.dataset;
  mPoster.innerHTML = data.poster ? `<img src="${data.poster}" alt="${data.title}">` : '<div class="placeholder">🎞️</div>';
  mTitle.textContent = data.title;
  mMeta.textContent = `${data.year || '—'} • ${data.rating || '—'} ⭐ • ${data.source.toUpperCase()}`;
  mOverview.textContent = data.overview || 'Sem sinopse disponível.';
  mDetails.href = data.url || '#';

  // Trailer — chama backend para pegar chave real do YouTube
  const tmdbId = data.tmdbId;
  mTrailer.href = '#';
  mTrailer.textContent = '🎥 Trailer';
  if (tmdbId) {
    fetch(`/api/trailer?tmdb_id=${encodeURIComponent(tmdbId)}`)
      .then(r => r.json())
      .then(j => {
        if (j.ok && j.url) { mTrailer.href = j.url; }
        else { mTrailer.href = `https://www.youtube.com/results?search_query=${encodeURIComponent(data.title + ' trailer')}`; }
      })
      .catch(() => {
        mTrailer.href = `https://www.youtube.com/results?search_query=${encodeURIComponent(data.title + ' trailer')}`;
      });
  } else {
    mTrailer.href = `https://www.youtube.com/results?search_query=${encodeURIComponent(data.title + ' trailer')}`;
  }

  // Favorito no modal
  mFavBtn.dataset.id = data.id;
  mFavBtn.classList.toggle('active', isFav(data.id));
  mFavBtn.onclick = () => {
    const active = toggleFav(data.id);
    mFavBtn.classList.toggle('active', active);
    const btn = card.querySelector('.fav-btn');
    if (btn) btn.classList.toggle('active', active);
  };

  modal.style.display = 'flex';
}
mClose?.addEventListener('click', () => modal.style.display = 'none');
modal?.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });

document.addEventListener('click', (e) => {
  const opener = e.target.closest('.open-modal');
  if (!opener) return;
  const card = e.target.closest('.card');
  if (card) openModalFromCard(card);
});

window.addEventListener('load', syncFavButtons);
