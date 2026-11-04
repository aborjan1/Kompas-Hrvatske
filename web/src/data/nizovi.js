// Time series for the chart panel (web/public/data/nizovi.json, pipeline/nizovi.py):
// population, unemployment, income, income tax, property sales and property income over
// the years. Loaded once, the first time a chart asks for it. Budget series for the Novac
// tema stay in proracuni.json.

import { writable } from 'svelte/store';
import { sPrijevodom } from './prijevod.js';

/**
 * @typedef {object} Serija
 * @property {string} naziv
 * @property {string} tema
 * @property {string} jedinica Unit of the values, e.g. 'EUR', '%', 'osoba', 'broj'.
 * @property {number} decimale
 * @property {{ mnozitelj: number, jedinica: string } | null} po_stanovniku How to show it per
 *   resident (divided by the 2021 census), or null when that makes no sense (rates).
 * @property {string} izvor Key into meta.json `izvori`.
 * @property {number[]} godine
 * @property {string[]} razine
 * @property {string} napomena
 */

/**
 * @typedef {object} Nizovi
 * @property {Record<string, Serija>} serije
 * @property {Record<string, Record<string, (number | null)[]>>} podrucja Area code → series
 *   id → one value per year of that series ("HR" for the country).
 */

/** Series shown for each tema, in order (Novac has its own budget charts). */
export const SERIJE_TEME = {
  ljudi: ['stanovnistvo', 'neto_dohodak', 'nezaposlenost'],
  porezi: ['porez_na_dohodak'],
  imovina: ['kupoprodaje_nekretnina', 'porez_na_promet_nekretnina', 'prihodi_od_imovine'],
  nabava: ['javna_nabava'],
};

/**
 * Whether an area has any chart for a tema. Novac (budget) and Nabava (graph of links)
 * have charts of their own, and until the series load the answer is yes.
 * @param {Nizovi | null} n
 * @param {string} tema
 * @param {string | undefined} sifra
 */
export function imaGrafove(n, tema, sifra) {
  if (tema === 'novac' || tema === 'nabava' || !n) return true;
  return SERIJE_TEME[tema].some((sid) => n.podrucja[sifra]?.[sid]?.some((v) => v !== null));
}

/** @type {import('svelte/store').Writable<{ podaci: Nizovi | null, greska: boolean }>} */
const store = writable({ podaci: null, greska: false });

/** @type {import('svelte/store').Readable<{ podaci: Nizovi | null, greska: boolean }>} */
export const nizovi = sPrijevodom(store, (n, en) => ({
  ...n,
  serije: Object.fromEntries(Object.entries(n.serije).map(([k, s]) => [k, { ...s, ...(en.serije[k] ?? {}) }])),
}));

let zatrazeno = false;

export function ucitajNizove() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/nizovi.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`nizovi.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((podaci) => store.set({ podaci, greska: false }))
    .catch((error) => {
      console.error(error);
      store.set({ podaci: null, greska: true });
    });
}
