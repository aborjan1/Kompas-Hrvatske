// Loads the exported data files (docs/format-podataka.md) once and exposes them as a
// store. Cities and municipalities (jls.json) load only after the user first leaves
// country level, since most visits never need them.

import { writable } from 'svelte/store';
import { view } from '../state.js';

// TODO: switch to 'data/' once the pipeline output is on main, then delete public/mock/.
const BASE_URL = `${import.meta.env.BASE_URL}mock/`;

/**
 * @typedef {object} Podrucje
 * @property {string} sifra
 * @property {string} naziv
 * @property {'drzava' | 'zupanija' | 'grad' | 'opcina'} vrsta
 * @property {string | null} nadredeno Parent area code; "HR" for counties.
 * @property {Record<string, number | null>} pokazatelji
 * @property {Record<string, number | null>} po_stanovniku
 * @property {Record<string, number>} rang 1 = largest value; per-capita ranks use the `<key>_po_stanovniku` key.
 * @property {string[]} slicni
 */

/**
 * @typedef {object} Pokazatelj One entry of meta.json `pokazatelji`.
 * @property {string} naziv
 * @property {string} tema
 * @property {string} jedinica
 * @property {number} decimale
 * @property {{ mnozitelj: number, jedinica: string } | null} po_stanovniku
 * @property {string[]} razine
 * @property {string} izvor Key into meta.json `izvori`.
 * @property {string} godina Free text, e.g. "2025" or "stanje 31.05.2023".
 * @property {string} [napomena]
 */

/**
 * @typedef {object} Podaci Each field is null until its file has loaded.
 * @property {{ teme: Record<string, string>, pokazatelji: Record<string, Pokazatelj>, izvori: Record<string, any>, napomene: string[] } | null} meta
 * @property {Podrucje | null} drzava
 * @property {Record<string, Podrucje> | null} zupanije
 * @property {Record<string, Podrucje> | null} jls
 * @property {string | null} greska Set when a file failed to load.
 */

/** @type {import('svelte/store').Writable<Podaci>} */
const store = writable({ meta: null, drzava: null, zupanije: null, jls: null, greska: null });

/** @type {import('svelte/store').Readable<Podaci>} */
export const podaci = { subscribe: store.subscribe };

Promise.all([dohvati('meta'), dohvati('drzava'), dohvati('zupanije')])
  .then(([meta, drzava, zupanije]) =>
    store.update((p) => ({ ...p, meta, drzava, zupanije: zupanije.podrucja })),
  )
  .catch(prijaviGresku);

let jlsZatrazen = false;
view.subscribe(({ razina }) => {
  if (razina === 'drzava' || jlsZatrazen) return;
  jlsZatrazen = true;
  dohvati('jls')
    .then((jls) => store.update((p) => ({ ...p, jls: jls.podrucja })))
    .catch(prijaviGresku);
});

async function dohvati(naziv) {
  const odgovor = await fetch(`${BASE_URL}${naziv}.json`);
  if (!odgovor.ok) throw new Error(`${naziv}.json: HTTP ${odgovor.status}`);
  return odgovor.json();
}

function prijaviGresku(error) {
  console.error(error);
  store.update((p) => ({ ...p, greska: 'Podaci se nisu učitali. Osvježite stranicu.' }));
}

/**
 * The area for a level and code, or null if it is unknown or not loaded yet.
 * @param {Podaci} p
 * @param {import('../state.js').Razina} razina
 * @param {string | null} sifra
 * @returns {Podrucje | null}
 */
export function nadjiPodrucje(p, razina, sifra) {
  if (razina === 'drzava') return p.drzava;
  if (razina === 'zupanija') return p.zupanije?.[sifra] ?? null;
  return p.jls?.[sifra] ?? null;
}

/**
 * The value to show for one indicator of an area: per capita when asked for and the
 * indicator has one, otherwise the total.
 * @param {Podrucje} podrucje
 * @param {string} kljuc
 * @param {Pokazatelj} pokazatelj
 * @param {import('../state.js').Mjera} mjera
 */
export function ocitaj(podrucje, kljuc, pokazatelj, mjera) {
  const poStanovniku = mjera === 'po-stanovniku' && pokazatelj.po_stanovniku !== null;
  return {
    value: (poStanovniku ? podrucje.po_stanovniku[kljuc] : podrucje.pokazatelji[kljuc]) ?? null,
    jedinica: poStanovniku ? pokazatelj.po_stanovniku.jedinica : pokazatelj.jedinica,
    // Per-capita amounts are small, so whole euros or one decimal read better than the total's decimals.
    decimale: poStanovniku ? (pokazatelj.jedinica === 'EUR' ? 0 : 1) : pokazatelj.decimale,
    rang: podrucje.rang[poStanovniku ? `${kljuc}_po_stanovniku` : kljuc] ?? null,
    poStanovniku,
  };
}
