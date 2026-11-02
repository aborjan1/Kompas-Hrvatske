// Local budgets by year and expenditure by function (web/public/data/proracuni.json,
// docs/format-podataka.md). Loaded once, the first time a panel asks for it, since
// only the Novac tema needs it.

import { writable } from 'svelte/store';

/**
 * @typedef {object} ProracunPodrucja
 * @property {number[]} prihodi Revenue per year, same order as `godine`.
 * @property {number[]} rashodi
 * @property {number[]} ulaganja
 * @property {Record<string, number>} funkcije Expenditure by COFOG function ("01"–"10"), last year.
 */

/**
 * @typedef {object} Proracuni
 * @property {number[]} godine
 * @property {string} napomena
 * @property {Record<string, string>} funkcije Official COFOG names by code.
 * @property {Record<string, ProracunPodrucja>} podrucja Keyed by area code; "HR" for the country.
 */

/** @type {import('svelte/store').Writable<{ podaci: Proracuni | null, greska: boolean }>} */
const store = writable({ podaci: null, greska: false });

/** @type {import('svelte/store').Readable<{ podaci: Proracuni | null, greska: boolean }>} */
export const proracuni = { subscribe: store.subscribe };

let zatrazeno = false;

export function ucitajProracune() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/proracuni.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`proracuni.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((podaci) => store.set({ podaci, greska: false }))
    .catch((error) => {
      console.error(error);
      store.set({ podaci: null, greska: true });
    });
}
