// Biggest suppliers and their links to other cities and municipalities, per area
// (web/public/data/nabava.json, pipeline/nabava.py). Loaded once, the first time the
// Nabava tema needs it.

import { writable } from 'svelte/store';
import { sPrijevodom } from './prijevod.js';

/**
 * @typedef {object} Dobavljac
 * @property {string} naziv
 * @property {number} iznos EUR over the period.
 * @property {number | null} udio Share of the area's contract value, %.
 * @property {number} drugih_jls How many other cities and municipalities have contracts with it.
 * @property {string[]} drugi Up to six of them (codes), largest first.
 */

/**
 * @typedef {object} Nabava
 * @property {string} razdoblje E.g. "2019.–2023.".
 * @property {string} napomena
 * @property {Record<string, { ugovora: number, dobavljaci: Dobavljac[] }>} podrucja
 */

/** @type {import('svelte/store').Writable<{ podaci: Nabava | null, greska: boolean }>} */
const store = writable({ podaci: null, greska: false });

/** @type {import('svelte/store').Readable<{ podaci: Nabava | null, greska: boolean }>} */
export const nabava = sPrijevodom(store, (n, en) => ({ ...n, napomena: en.nabava.napomena, razdoblje: en.nabava.razdoblje }));

let zatrazeno = false;

export function ucitajNabavu() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/nabava.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`nabava.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((podaci) => store.set({ podaci, greska: false }))
    .catch((error) => {
      console.error(error);
      store.set({ podaci: null, greska: true });
    });
}
