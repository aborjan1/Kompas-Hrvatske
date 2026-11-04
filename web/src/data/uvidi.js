// „Što je neobično ovdje” (web/public/data/uvidi.json, pipeline/uvidi.py): per city or
// municipality, the indicators where it differs most from others of the same type in the
// typology. Loaded once, the first time a city or municipality is opened.

import { writable } from 'svelte/store';

/**
 * @typedef {object} Uvid
 * @property {string} kljuc Indicator key in meta.json `pokazatelji`.
 * @property {boolean} po_stanovniku Whether `vrijednost` and `slicni` are per resident.
 * @property {number} vrijednost
 * @property {number} slicni Median of the same type.
 * @property {number} z Robust z-score within the type (log scale for amounts).
 * @property {'vise' | 'manje'} smjer
 */

/**
 * @typedef {object} Uvidi
 * @property {number} prag
 * @property {Record<string, number>} tipovi How many cities and municipalities each type has.
 * @property {Record<string, Uvid[]>} podrucja
 */

/** @type {import('svelte/store').Writable<{ podaci: Uvidi | null, greska: boolean }>} */
const store = writable({ podaci: null, greska: false });

/** @type {import('svelte/store').Readable<{ podaci: Uvidi | null, greska: boolean }>} */
export const uvidi = { subscribe: store.subscribe };

let zatrazeno = false;

export function ucitajUvide() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/uvidi.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`uvidi.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((podaci) => store.set({ podaci, greska: false }))
    .catch((error) => {
      console.error(error);
      store.set({ podaci: null, greska: true });
    });
}
