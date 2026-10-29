// Turns the current view (razina, tema, mjera) into numbers per area code. The map
// colours areas from this and the panels show its title and source, so the meaning
// of each tema lives in one place and the map never needs to know about temas.
//
// For the country the values are per county. For a selected county, and for a city or
// municipality in it, they are per JLS of that county, so the map ranks its cities and
// municipalities against each other. A county whose tema has nothing for its cities
// (Imovina) falls back to county values. `razina` says which.

import { derived } from 'svelte/store';
import { view } from '../state.js';
import { ocitaj, podaci } from './podaci.js';
import { JEDNOSTAVNI_NAZIVI, TEME_POKAZATELJI } from './teme.js';

/**
 * @typedef {object} Indicator
 * @property {string} kljuc Indicator key in meta.json `pokazatelji`.
 * @property {'zupanija' | 'jls'} razina Which areas `values` are keyed by.
 * @property {string} title Indicator name shown in the legend and panel.
 * @property {string} unit Unit from meta.json, e.g. 'EUR', 'EUR po stanovniku', '%'.
 * @property {number} decimale Decimals for formatVrijednost() in format.js.
 * @property {string} godina Period of the data, free text ("2025", "stanje 31.05.2023").
 * @property {string} izvor Publisher and dataset ("Državni zavod za statistiku – …"), shown under the map.
 * @property {string | null} poveznica Link to the dataset.
 * @property {boolean} poStanovniku Whether values are per capita.
 * @property {boolean} imaPoStanovniku Whether the indicator has a per-capita variant at all.
 * @property {string[]} boje The tema's colour ramp for the map classes, light → dark.
 * @property {Record<string, number | null>} values Keyed by area code (`sifra`).
 */

/**
 * Null while data is loading, or when the tema has no indicator at the coloured level
 * (e.g. Imovina for cities and municipalities).
 * @type {import('svelte/store').Readable<Indicator | null>}
 */
export const indicator = derived([view, podaci], ([v, p]) => {
  if (!p.meta) return null;

  const kljucJls = TEME_POKAZATELJI[v.tema].karta.jls;
  const jlsMoguce = Boolean(kljucJls && p.meta.pokazatelji[kljucJls]?.razine.includes('jls'));
  if (v.razina === 'jls' && !jlsMoguce) return null;
  // Until jls.json has loaded, a county shows its own value rather than nothing.
  const razina = v.razina !== 'drzava' && jlsMoguce && p.jls ? 'jls' : 'zupanija';
  const kljuc = TEME_POKAZATELJI[v.tema].karta[razina];
  const pokazatelj = kljuc ? p.meta.pokazatelji[kljuc] : null;
  if (!pokazatelj?.razine.includes(razina)) return null;

  const podrucja = razina === 'zupanija' ? p.zupanije : p.jls;
  if (!podrucja) return null;
  const zupanija = v.razina === 'zupanija' ? v.podrucje : p.jls?.[v.podrucje]?.nadredeno;

  let jedinica = pokazatelj.jedinica;
  let decimale = pokazatelj.decimale;
  let poStanovniku = false;
  /** @type {Record<string, number | null>} */
  const values = {};
  for (const podrucje of Object.values(podrucja)) {
    if (razina === 'jls' && podrucje.nadredeno !== zupanija) continue;
    const o = ocitaj(podrucje, kljuc, pokazatelj, v.mjera);
    values[podrucje.sifra] = o.value;
    jedinica = o.jedinica;
    decimale = o.decimale;
    poStanovniku = o.poStanovniku;
  }

  const izvor = p.meta.izvori[pokazatelj.izvor];
  return {
    kljuc,
    razina,
    title: JEDNOSTAVNI_NAZIVI[kljuc] ?? pokazatelj.naziv,
    unit: jedinica,
    decimale,
    godina: pokazatelj.godina,
    izvor: izvor ? `${izvor.izdavatelj} – ${izvor.naziv}` : pokazatelj.izvor,
    poveznica: izvor?.poveznica ?? null,
    poStanovniku,
    imaPoStanovniku: pokazatelj.po_stanovniku !== null,
    boje: TEME_POKAZATELJI[v.tema].boje,
    values,
  };
});
