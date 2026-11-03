// Interface language: Croatian (default) or English, for EU readers and investors.
// The choice comes from the link (`lang=en` in the hash, src/url.js), else from the
// last choice in this browser, else Croatian. It is never guessed from the browser's
// language, so Croatian users with an English browser still get Croatian.
//
// Texts sit next to each other in the code: t('Grafovi', 'Charts'). Panels are
// remounted when the language changes (App.svelte), so plain calls are enough there;
// the map listens to `jezik` itself. Data texts (indicator names and explanations) come
// from en.json (src/data/prijevod.js).

import { get, writable } from 'svelte/store';

/** @typedef {'hr' | 'en'} Jezik */

export const JEZICI = /** @type {const} */ (['hr', 'en']);
const SPREMLJENO = 'kh-jezik';

/** @param {string} hash */
export function jezikIzHasha(hash) {
  const lang = new URLSearchParams(hash.split('?')[1] ?? '').get('lang');
  return JEZICI.includes(lang) ? /** @type {Jezik} */ (lang) : null;
}

function spremljeni() {
  try {
    const j = localStorage.getItem(SPREMLJENO);
    return JEZICI.includes(j) ? /** @type {Jezik} */ (j) : null;
  } catch {
    return null;
  }
}

const pocetni = typeof location === 'undefined' ? 'hr' : (jezikIzHasha(location.hash) ?? spremljeni() ?? 'hr');

/** @type {import('svelte/store').Writable<Jezik>} */
const store = writable(pocetni);

/** @type {import('svelte/store').Readable<Jezik>} */
export const jezik = { subscribe: store.subscribe };

/** @param {Jezik} j */
export function setJezik(j) {
  if (!JEZICI.includes(j)) throw new Error(`Unknown jezik ${JSON.stringify(j)}`);
  try {
    localStorage.setItem(SPREMLJENO, j);
  } catch {
    // Private mode or blocked storage: the choice lasts until the page closes.
  }
  if (get(store) !== j) store.set(j);
}

/** Whether the interface is in English right now. */
export const engleski = () => get(store) === 'en';

/**
 * The text for the current language.
 * @param {string} hr
 * @param {string} en
 */
export const t = (hr, en) => (engleski() ? en : hr);

/** Locale for Intl formatting. */
export const lokal = () => (engleski() ? 'en-GB' : 'hr-HR');

/**
 * A year as written in running text: "2025." in Croatian, "2025" in English.
 * @param {string | number} g
 */
export const god = (g) => (engleski() ? `${g}` : `${g}.`);

/** A range of years: "2019.–2023." or "2019–2023". */
export const raspon = (od, doGod) => `${god(od)}–${god(doGod)}`;

// The page itself follows: <html lang>, title and description for search engines and
// screen readers.
const OPIS = {
  hr: 'Kompas Hrvatske: otvoreni podaci o županijama, gradovima i općinama Hrvatske na interaktivnoj karti.',
  en: 'Croatia Compass: open data on Croatian counties, cities and municipalities on an interactive map.',
};
if (typeof document !== 'undefined') {
  store.subscribe((j) => {
    document.documentElement.lang = j;
    document.title = j === 'en' ? 'Croatia Compass (Kompas Hrvatske)' : 'Kompas Hrvatske';
    document.querySelector('meta[name="description"]')?.setAttribute('content', OPIS[j]);
  });
}
