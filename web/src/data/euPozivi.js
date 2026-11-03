// Planned and open EU calls for 2026 in which cities, municipalities or counties can take part
// (web/public/data/eu-pozivi.json, pipeline/eu_pozivi.py). Loaded once, when first needed.

import { writable } from 'svelte/store';
import { engleski, t } from '../jezik.js';
import { sPrijevodom } from './prijevod.js';

/**
 * @typedef {object} Poziv
 * @property {string} id
 * @property {'PKK' | 'ITP' | 'ULJP'} program
 * @property {string} naziv
 * @property {string} vrsta Procedure, e.g. "Otvoreni (privremeni)".
 * @property {number | null} iznos EUR for the whole call.
 * @property {string | null} pocetak "2026-11-06", or "2026-11" when the plan gives only a month.
 * @property {string | null} kraj Same format; null when the plan has no closing date.
 * @property {boolean} samo_mjesec
 * @property {string} podrucje Area as written in the plan.
 * @property {string[] | null} zupanije County codes the call covers; null = all of Croatia.
 * @property {'prijavitelj' | 'partner' | null} jls Role of cities and municipalities.
 * @property {'prijavitelj' | 'partner' | null} zupanija Role of counties.
 * @property {string[]} imenovani Cities or municipalities the call is meant for by name.
 * @property {string} prijavitelji Eligible applicants as written in the plan.
 * @property {string | null} napomena
 */

/** @type {import('svelte/store').Writable<{ podaci: { pozivi: Poziv[], napomena: string } | null, greska: boolean }>} */
const store = writable({ podaci: null, greska: false });

// In English: translated name where en.json has one, procedure and programme in English;
// who may apply stays as written in the plan (`prijavitelji_izvorno`).
export const euPozivi = sPrijevodom(store, (d, en) => ({
  ...d,
  napomena: en.eu_pozivi.napomena,
  pozivi: d.pozivi.map((p) => {
    const e = en.eu_pozivi.pozivi[p.id];
    return {
      ...p,
      naziv: e?.naziv ?? p.naziv,
      napomena: e?.napomena ?? p.napomena,
      vrsta: en.eu_pozivi.vrste[p.vrsta] ?? p.vrsta,
      program_naziv: en.eu_pozivi.programi[p.program] ?? p.program,
      podrucje: p.zupanije === null ? 'Croatia' : p.podrucje,
    };
  }),
}));

let zatrazeno = false;

export function ucitajEuPozive() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/eu-pozivi.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`eu-pozivi.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((podaci) => store.set({ podaci, greska: false }))
    .catch((error) => {
      console.error(error);
      store.set({ podaci: null, greska: true });
    });
}

const MJESECI = ['siječanj', 'veljača', 'ožujak', 'travanj', 'svibanj', 'lipanj', 'srpanj', 'kolovoz', 'rujan', 'listopad', 'studeni', 'prosinac'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-11-06" → "6. 11. 2026." / "6 November 2026", "2026-11" → "studeni 2026." / "November 2026" */
export function datumTekst(d) {
  if (!d) return '';
  const [g, m, dan] = d.split('-');
  if (engleski()) return dan ? `${Number(dan)} ${MONTHS[Number(m) - 1]} ${g}` : `${MONTHS[Number(m) - 1]} ${g}`;
  return dan ? `${Number(dan)}. ${Number(m)}. ${g}.` : `${MJESECI[Number(m) - 1]} ${g}.`;
}

/**
 * Where the call stands today: open, coming, or closed (closed calls are hidden).
 * A month-only start counts from the first of the month.
 * @param {Poziv} p
 * @param {Date} danas
 */
export function stanje(p, danas = new Date()) {
  const dan = danas.toISOString().slice(0, 10);
  const pocetak = p.pocetak && (p.pocetak.length === 7 ? `${p.pocetak}-01` : p.pocetak);
  const kraj = p.kraj && (p.kraj.length === 7 ? `${p.kraj}-31` : p.kraj);
  const d = (x) => datumTekst(x);
  if (kraj && kraj < dan) return { kod: 'zatvoren', tekst: t(`Zatvoren ${d(p.kraj)}`, `Closed ${d(p.kraj)}`) };
  if (p.samo_mjesec && !kraj) {
    return { kod: 'planiran', tekst: t(`Objava planirana: ${d(p.pocetak)}`, `Planned for ${d(p.pocetak)}`) };
  }
  if (pocetak && pocetak > dan) return { kod: 'uskoro', tekst: t(`Otvara se ${d(p.pocetak)}`, `Opens ${d(p.pocetak)}`) };
  if (kraj) return { kod: 'otvoren', tekst: t(`Otvoren do ${d(p.kraj)}`, `Open until ${d(p.kraj)}`) };
  return { kod: 'otvoren', tekst: t('Otvoren', 'Open') };
}
