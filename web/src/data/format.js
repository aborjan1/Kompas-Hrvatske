// Number formatting for the panels, driven by `jedinica` and `decimale` from meta.json.
// Croatian conventions: 1.234.567,8 and a space before units, including %.
// English (src/jezik.js): 1,234,567.8, "€2.9 bn", "3.3%", units in English.

import { engleski, lokal } from '../jezik.js';

// Units that read better without a label ("3.871.833", not "3.871.833 osoba").
const SKRIVENE_JEDINICE = new Set(['osoba', 'broj']);

// Units from meta.json and nizovi.json in English. Missing ones are shown as they are.
const JEDINICE_EN = {
  ' po stanovniku': ' per resident',
  'na 1.000 stanovnika': 'per 1,000 residents',
  'st./km²': 'people/km²',
  'p.b.': 'pp',
};

/**
 * A unit as a label in the current language: " po stanovniku" → " per resident".
 * @param {string} jedinica
 */
export function nazivJedinice(jedinica) {
  return engleski() ? (JEDINICE_EN[jedinica] ?? jedinica) : jedinica;
}

/**
 * @param {number} n
 * @returns {string} "1 projekt", "3 projekta", "12 projekata" / "1 project", "12 projects".
 */
export function brojProjekata(n) {
  if (engleski()) return `${broj(0).format(n)} ${n === 1 ? 'project' : 'projects'}`;
  const zadnja = n % 10;
  const zadnjeDvije = n % 100;
  const oblik =
    zadnja === 1 && zadnjeDvije !== 11 ? 'projekt'
    : zadnja >= 2 && zadnja <= 4 && (zadnjeDvije < 12 || zadnjeDvije > 14) ? 'projekta'
    : 'projekata';
  return `${broj(0).format(n)} ${oblik}`;
}

const formati = new Map();
/**
 * Number format for the current language, cached.
 * @param {number} decimale
 */
export function broj(decimale) {
  const kljuc = `${lokal()}/${decimale}`;
  if (!formati.has(kljuc)) {
    formati.set(
      kljuc,
      new Intl.NumberFormat(lokal(), { minimumFractionDigits: decimale, maximumFractionDigits: decimale }),
    );
  }
  return formati.get(kljuc);
}

// Millions and billions: "563 mil.", "1,1 mlrd.", never "563,0 mil.".
const skraceno = (v) => new Intl.NumberFormat(lokal(), { maximumFractionDigits: 1 }).format(v);

/**
 * @param {number | null} value Raw value from the data files.
 * @param {string} jedinica Unit from meta.json, e.g. "EUR", "%", "EUR po stanovniku".
 * @param {number} decimale
 * @returns {string} E.g. "2,9 mlrd. €", "1.076 € po stanovniku", "3,3 %", or "nema podatka";
 *   in English "€2.9 bn", "€1,076 per resident", "3.3%", "no data".
 */
export function formatVrijednost(value, jedinica, decimale) {
  const en = engleski();
  if (value === null || !Number.isFinite(value)) return en ? 'no data' : 'nema podatka';

  if (jedinica.startsWith('EUR')) {
    const ostatak = jedinica.slice(3); // " po stanovniku", "/m²" or ""
    const iznos = Math.abs(value);
    if (en) {
      const kraj = JEDINICE_EN[ostatak] ?? ostatak;
      const znak = value < 0 ? '−' : '';
      if (iznos >= 1e9) return `${znak}€${skraceno(iznos / 1e9)} bn${kraj}`;
      if (iznos >= 1e6) return `${znak}€${skraceno(iznos / 1e6)} m${kraj}`;
      return `${znak}€${broj(decimale).format(iznos)}${kraj}`;
    }
    if (iznos >= 1e9) return `${skraceno(value / 1e9)} mlrd. €${ostatak}`;
    if (iznos >= 1e6) return `${skraceno(value / 1e6)} mil. €${ostatak}`;
    return `${broj(decimale).format(value)} €${ostatak}`;
  }

  const tekst = broj(decimale).format(value);
  if (SKRIVENE_JEDINICE.has(jedinica)) return tekst;
  if (jedinica === 'godina') return en ? `${tekst} yrs` : `${tekst} god.`;
  if (en) return jedinica === '%' ? `${tekst}%` : `${tekst} ${JEDINICE_EN[jedinica] ?? jedinica}`;
  return `${tekst} ${jedinica}`;
}

/**
 * A share or change in whole percent, for the panels: "12 %" / "12%".
 * @param {number} v
 * @param {{ predznak?: boolean }} [opcije] `predznak`: always show + or −.
 */
export function postotak(v, { predznak = false } = {}) {
  const f = new Intl.NumberFormat(lokal(), { maximumFractionDigits: 0, signDisplay: predznak ? 'always' : 'auto' });
  return engleski() ? `${f.format(v)}%` : `${f.format(v)} %`;
}
