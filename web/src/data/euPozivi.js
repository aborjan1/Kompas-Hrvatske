// Planned and open EU calls for 2026 in which cities, municipalities or counties can take part
// (web/public/data/eu-pozivi.json, pipeline/eu_pozivi.py). Loaded once, when first needed.

import { writable } from 'svelte/store';

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

export const euPozivi = { subscribe: store.subscribe };

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

/** "2026-11-06" → "6. 11. 2026.", "2026-11" → "studeni 2026." */
export function datumTekst(d) {
  if (!d) return '';
  const [g, m, dan] = d.split('-');
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
  if (kraj && kraj < dan) return { kod: 'zatvoren', tekst: `Zatvoren ${datumTekst(p.kraj)}` };
  if (p.samo_mjesec && !kraj) {
    return { kod: 'planiran', tekst: `Objava planirana: ${datumTekst(p.pocetak)}` };
  }
  if (pocetak && pocetak > dan) return { kod: 'uskoro', tekst: `Otvara se ${datumTekst(p.pocetak)}` };
  return { kod: 'otvoren', tekst: kraj ? `Otvoren do ${datumTekst(p.kraj)}` : 'Otvoren' };
}
