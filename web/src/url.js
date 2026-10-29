// Keeps the shared state and the URL hash in step, so every view has its own link and
// the browser's Back and Forward move between areas. Same values as the state:
//   #/?tema=novac&mjera=ukupno
//   #/zupanija/05?tema=novac&mjera=po-stanovniku
//   #/jls/<sifra>?tema=porezi&mjera=ukupno
// A new area adds a history entry; a new tema or mjera replaces the current one, so
// Back steps through areas rather than through every tema click. A hash, not a path,
// so GitHub Pages needs no server setup.

import { derived, get } from 'svelte/store';
import { MJERE, TEME, selectArea, setView, view } from './state.js';
import { podaci } from './data/podaci.js';

/**
 * Reads a view from a hash. Unknown or missing tema and mjera keep `fallback`'s values;
 * anything that isn't a county or JLS path is the country.
 * @param {string} hash E.g. "#/zupanija/05?tema=novac&mjera=ukupno".
 * @param {import('./state.js').View} fallback
 * @returns {import('./state.js').View}
 */
export function parseHash(hash, fallback) {
  const [path, query = ''] = hash.replace(/^#/, '').split('?');
  const [razina, podrucje] = path.split('/').filter(Boolean);
  const params = new URLSearchParams(query);
  const tema = params.get('tema');
  const mjera = params.get('mjera');
  const podrucjeJe = (razina === 'zupanija' || razina === 'jls') && Boolean(podrucje);
  return {
    razina: podrucjeJe ? razina : 'drzava',
    podrucje: podrucjeJe ? decodeURIComponent(podrucje) : null,
    tema: TEME.includes(tema) ? tema : fallback.tema,
    mjera: MJERE.includes(mjera) ? mjera : fallback.mjera,
  };
}

/**
 * @param {import('./state.js').View} v
 * @returns {string}
 */
export function formatHash({ razina, podrucje, tema, mjera }) {
  const path = razina === 'drzava' ? '/' : `/${razina}/${encodeURIComponent(podrucje)}`;
  return `#${path}?tema=${tema}&mjera=${mjera}`;
}

/**
 * Starts the sync. Call before mounting the app, so the map's intro already lands on
 * the area in the link.
 */
export function startUrlSync() {
  setView(parseHash(location.hash, get(view)));
  // Normalise the link (fills in tema and mjera, drops anything unknown).
  history.replaceState(history.state, '', formatHash(get(view)));

  let previous = get(view);
  let replaceNext = false;
  view.subscribe((v) => {
    const hash = formatHash(v);
    const novoPodrucje = v.razina !== previous.razina || v.podrucje !== previous.podrucje;
    previous = v;
    // Already there: the change came from the URL (startup, Back or Forward).
    if (hash === location.hash) return;
    if (novoPodrucje && !replaceNext) history.pushState(null, '', hash);
    else history.replaceState(null, '', hash);
    replaceNext = false;
  });

  // Back, Forward and a hash typed into the address bar. The browser has already made
  // the history entry, so a link that needs normalising is fixed in place.
  addEventListener('popstate', () => {
    replaceNext = true;
    setView(parseHash(location.hash, get(view)));
    replaceNext = false;
  });

  // A code the data doesn't know (a stale or mistyped link) falls back to the country,
  // once the file that could have it has loaded. It replaces the bad entry, so Back
  // doesn't lead to it again.
  derived([view, podaci], ([v, p]) => {
    if (v.razina === 'drzava') return true;
    const podrucja = v.razina === 'zupanija' ? p.zupanije : p.jls;
    return !podrucja || Object.hasOwn(podrucja, v.podrucje);
  }).subscribe((poznato) => {
    if (poznato) return;
    replaceNext = true;
    selectArea('drzava');
  });
}
