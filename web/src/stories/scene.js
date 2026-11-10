// Turns a story scene from price.json into a view and a sentence. A scene names its
// area by rule ("the county with the largest X") rather than by code, and its text has
// placeholders filled from the data, so stories stay true when the data is refreshed:
//   {naziv}      the area's name
//   {vrijednost} the scene's indicator for that area, formatted, in the scene's mjera
//   {zupanija}   the county a city or municipality belongs to

import { ocitaj } from '../data/podaci.js';
import { formatVrijednost } from '../data/format.js';

/**
 * @typedef {object} Scena
 * @property {import('../state.js').Razina} razina
 * @property {'najveci' | 'najmanji'} [odabir] How to pick the area (not for drzava).
 * @property {string} [sifra] A fixed area instead of `odabir`.
 * @property {string} [pokazatelj] Indicator key for `odabir` and {vrijednost}; the map is
 *   coloured by it too, at whichever level it has (src/data/kartaPrice.js).
 * @property {string} [karta] Indicator the map is coloured by, for a scene without
 *   `pokazatelj` or when the map should show something else.
 * @property {import('../state.js').Tema} tema
 * @property {import('../state.js').Mjera} mjera
 * @property {boolean} [eu] Show the EU projects layer.
 * @property {string} tekst
 * @property {string} [tekst_en] The same sentence in English (same placeholders).
 */

/**
 * @typedef {object} Prica
 * @property {string} id
 * @property {string} naslov
 * @property {string} opis
 * @property {string} [naslov_en]
 * @property {string} [opis_en]
 * @property {Scena[]} scene
 */

/**
 * Whether the data this scene needs has loaded.
 * @param {import('../data/podaci.js').Podaci} p
 * @param {Scena} scena
 */
export function imaPodatke(p, scena) {
  return Boolean(p.meta && p.drzava && p.zupanije && (scena.razina !== 'jls' || p.jls));
}

/**
 * @param {import('../data/podaci.js').Podaci} p Loaded data (see imaPodatke).
 * @param {Scena} scena
 * @returns {{ view: import('../state.js').View, tekst: string } | null} Null if no area fits.
 */
export function rijesiScenu(p, scena) {
  const { razina, tema, mjera } = scena;
  const pokazatelj = scena.pokazatelj ? p.meta.pokazatelji[scena.pokazatelj] : null;
  const procitaj = (podrucje) => (pokazatelj ? ocitaj(podrucje, scena.pokazatelj, pokazatelj, mjera) : null);

  let podrucje;
  if (razina === 'drzava') podrucje = p.drzava;
  else if (scena.sifra) podrucje = (razina === 'zupanija' ? p.zupanije : p.jls)[scena.sifra];
  else podrucje = odaberi(Object.values(razina === 'zupanija' ? p.zupanije : p.jls), procitaj, scena.odabir);
  if (!podrucje) return null;

  const o = procitaj(podrucje);
  const zamjene = {
    naziv: podrucje.naziv,
    vrijednost: o ? formatVrijednost(o.value, o.jedinica, o.decimale) : '',
    zupanija: razina === 'jls' ? (p.zupanije[podrucje.nadredeno]?.naziv ?? '') : '',
  };
  return {
    view: { razina, podrucje: razina === 'drzava' ? null : podrucje.sifra, tema, mjera },
    tekst: scena.tekst.replace(/\{(\w+)\}/g, (_, kljuc) => zamjene[kljuc] ?? ''),
  };
}

// The area with the largest or smallest value; ties go to the first by name, so a
// story always picks the same one.
function odaberi(podrucja, procitaj, odabir) {
  const s = podrucja
    .map((podrucje) => ({ podrucje, value: procitaj(podrucje)?.value ?? null }))
    .filter((x) => x.value !== null)
    .sort((a, b) => (odabir === 'najmanji' ? a.value - b.value : b.value - a.value) || (a.podrucje.naziv_hr ?? a.podrucje.naziv).localeCompare(b.podrucje.naziv_hr ?? b.podrucje.naziv, 'hr'));
  return s[0]?.podrucje ?? null;
}
