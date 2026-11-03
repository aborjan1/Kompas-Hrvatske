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
import { TEME_POKAZATELJI, jednostavniNaziv } from './teme.js';
import { engleski, t } from '../jezik.js';

/**
 * @typedef {object} Indicator
 * @property {string} kljuc Indicator key in meta.json `pokazatelji`.
 * @property {'zupanija' | 'jls'} razina Which areas `values` are keyed by.
 * @property {string} title Indicator name shown in the legend and panel.
 * @property {string} objasnjenje What the number means, in plain words (meta.json).
 * @property {string} unit Unit from meta.json, e.g. 'EUR', 'EUR po stanovniku', '%'.
 * @property {number} decimale Decimals for formatVrijednost() in format.js.
 * @property {string} godina Period of the data, free text ("2025", "stanje 31.05.2023").
 * @property {string} izvor Publisher and dataset ("Državni zavod za statistiku – …"), shown under the map.
 * @property {string | null} poveznica Link to the dataset.
 * @property {string | null} stranica Site the dataset is published on ("data.gov.hr"), the link's text.
 * @property {string | null} preuzeto Download date, "29.10.2026.".
 * @property {{ naziv: string, poveznica: string } | null} dozvola Licence to link, only when the
 *   publisher states one (Open Licence, CC BY); sources without one claim none.
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
  // Combined sources (HBOR's 5 datasets, the 3 EU lists) keep link and date per part.
  const dio = izvor?.dijelovi?.[0] ?? izvor;
  const poveznica = izvor?.poveznica ?? dio?.poveznica ?? null;
  return {
    kljuc,
    razina,
    title: jednostavniNaziv(kljuc, pokazatelj),
    objasnjenje: pokazatelj.objasnjenje ?? '',
    unit: jedinica,
    decimale,
    godina: pokazatelj.godina,
    izvor: izvor ? `${izvor.izdavatelj} – ${izvor.naziv}` : pokazatelj.izvor,
    poveznica,
    stranica: poveznica ? new URL(poveznica).hostname.replace(/^www\./, '') : null,
    preuzeto: izvor ? datumPreuzimanja(izvor) : null,
    dozvola: dozvola(izvor?.licenca ?? dio?.licenca),
    poStanovniku,
    imaPoStanovniku: pokazatelj.po_stanovniku !== null,
    boje: TEME_POKAZATELJI[v.tema].boje,
    values,
  };
});

const MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');

/**
 * Download date of a source from meta.json `izvori`, as "29.10.2026." (English
 * "29 Oct 2026"). Combined sources take their first part's date.
 * @param {{ preuzeto?: string | null, dijelovi?: { preuzeto?: string | null }[] }} izvor
 * @returns {string | null}
 */
export function datumPreuzimanja(izvor) {
  const iso = izvor.preuzeto ?? izvor.dijelovi?.find((d) => d.preuzeto)?.preuzeto;
  if (!iso) return null;
  const [g, m, d] = iso.split('-');
  return engleski() ? `${Number(d)} ${MONTHS[Number(m) - 1]} ${g}` : `${Number(d)}.${Number(m)}.${g}.`;
}

/**
 * The licence to link next to the source, or null when the publisher states none: those
 * are cited by source only, without claiming the Open Licence (organisers, 29.10.2026.).
 * @param {string | undefined} licenca
 */
function dozvola(licenca) {
  if (licenca?.startsWith('Otvorena dozvola')) {
    return { naziv: t('Otvorena dozvola', 'Open Licence'), poveznica: 'https://data.gov.hr/otvorena-dozvola' };
  }
  if (licenca?.startsWith('CC BY')) {
    return { naziv: 'CC BY 4.0', poveznica: `https://creativecommons.org/licenses/by/4.0/${t('deed.hr', 'deed.en')}` };
  }
  return null;
}
