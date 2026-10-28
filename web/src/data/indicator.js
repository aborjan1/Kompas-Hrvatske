// Turns the current view (razina, tema, mjera) into numbers per area code. The map
// colours areas from this and the panels show its title and source, so the meaning
// of each tema lives in one place and the map never needs to know about temas.
//
// At country level the values are per county; inside a county they are per city and
// municipality of that county (the JLS layer, phase 4). `razina` says which.

import { derived } from 'svelte/store';
import { view } from '../state.js';
import { ocitaj, podaci } from './podaci.js';
import { TEME_POKAZATELJI } from './teme.js';

/**
 * @typedef {object} Indicator
 * @property {string} kljuc Indicator key in meta.json `pokazatelji`.
 * @property {'zupanija' | 'jls'} razina Which areas `values` are keyed by.
 * @property {string} title Indicator name shown in the legend and panel.
 * @property {string} unit Unit from meta.json, e.g. 'EUR', 'EUR po stanovniku', '%'.
 * @property {string} godina Period of the data, free text ("2025", "stanje 31.05.2023").
 * @property {string} izvor Dataset and publisher, shown under the map.
 * @property {boolean} poStanovniku Whether values are per capita.
 * @property {boolean} imaPoStanovniku Whether the indicator has a per-capita variant at all.
 * @property {Record<string, number | null>} values Keyed by area code (`sifra`).
 */

/**
 * Null while data is loading, or when the tema has no indicator at the coloured level
 * (e.g. Novac for cities and municipalities).
 * @type {import('svelte/store').Readable<Indicator | null>}
 */
export const indicator = derived([view, podaci], ([v, p]) => {
  if (!p.meta) return null;

  const razina = v.razina === 'drzava' ? 'zupanija' : 'jls';
  const kljuc = TEME_POKAZATELJI[v.tema].karta;
  const pokazatelj = p.meta.pokazatelji[kljuc];
  if (!pokazatelj?.razine.includes(razina)) return null;

  const podrucja = razina === 'zupanija' ? p.zupanije : p.jls;
  if (!podrucja) return null;
  const zupanija = v.razina === 'zupanija' ? v.podrucje : p.jls?.[v.podrucje]?.nadredeno;

  let jedinica = pokazatelj.jedinica;
  let poStanovniku = false;
  /** @type {Record<string, number | null>} */
  const values = {};
  for (const podrucje of Object.values(podrucja)) {
    if (razina === 'jls' && podrucje.nadredeno !== zupanija) continue;
    const o = ocitaj(podrucje, kljuc, pokazatelj, v.mjera);
    values[podrucje.sifra] = o.value;
    jedinica = o.jedinica;
    poStanovniku = o.poStanovniku;
  }

  const izvor = p.meta.izvori[pokazatelj.izvor];
  return {
    kljuc,
    razina,
    title: pokazatelj.naziv,
    unit: jedinica,
    godina: pokazatelj.godina,
    izvor: izvor ? `${izvor.naziv}, ${izvor.izdavatelj}` : pokazatelj.izvor,
    poStanovniku,
    imaPoStanovniku: pokazatelj.po_stanovniku !== null,
    values,
  };
});
