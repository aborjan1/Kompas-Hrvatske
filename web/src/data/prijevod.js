// English texts for the data (web/public/data/en.json, pipeline/prijevodi.py): indicator
// names and explanations, temas, typology, series, budget functions, county names and
// notes. Loaded only once English is chosen. The data stores (podaci, nizovi, proracuni,
// nabava, euPozivi) lay these over their Croatian texts, so components read one set of
// fields whatever the language. Names of cities, municipalities, suppliers and projects
// stay as published.

import { derived, writable } from 'svelte/store';
import { jezik } from '../jezik.js';

/** @type {import('svelte/store').Writable<any | null>} */
const ucitano = writable(null);
let zatrazeno = false;

function ucitaj() {
  if (zatrazeno) return;
  zatrazeno = true;
  fetch(`${import.meta.env.BASE_URL}data/en.json`)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`en.json: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((en) => ucitano.set(en))
    .catch((error) => {
      // Without it the data texts stay Croatian; the interface is still English.
      console.error(error);
      zatrazeno = false;
    });
}

/**
 * en.json while the interface is English and the file has loaded, otherwise null.
 * @type {import('svelte/store').Readable<any | null>}
 */
export const prijevod = derived([jezik, ucitano], ([j, en]) => (j === 'en' ? en : null));

jezik.subscribe((j) => {
  if (j === 'en') ucitaj();
});

/**
 * A store of `{ podaci, greska }` (nizovi, proracuni, …) with `prevedi(podaci, en)`
 * applied while English is on.
 * @template T
 * @param {import('svelte/store').Readable<{ podaci: T | null, greska: boolean }>} izvor
 * @param {(podaci: T, en: any) => T} prevedi
 */
export function sPrijevodom(izvor, prevedi) {
  return derived([izvor, prijevod], ([s, en]) => (en && s.podaci ? { ...s, podaci: prevedi(s.podaci, en) } : s));
}

/**
 * meta.json with English names and explanations.
 * @param {any} meta
 * @param {any} en
 */
export function prevediMeta(meta, en) {
  const pokazatelji = Object.fromEntries(
    Object.entries(meta.pokazatelji).map(([k, p]) => [k, { ...p, ...(en.pokazatelji[k] ?? {}) }]),
  );
  const izvori = Object.fromEntries(
    Object.entries(meta.izvori).map(([k, i]) => [k, { ...i, izdavatelj: en.izdavatelji[i.izdavatelj.trim()] ?? i.izdavatelj }]),
  );
  const tip = meta.tipologija;
  const tipologija = tip && {
    ...tip,
    naziv: en.tipologija.naziv,
    metoda: en.tipologija.metoda,
    obiljezja: en.tipologija.obiljezja,
    tipovi: Object.fromEntries(Object.entries(tip.tipovi).map(([k, v]) => [k, { ...v, ...(en.tipologija.tipovi[k] ?? {}) }])),
  };
  return { ...meta, teme: { ...meta.teme, ...en.teme }, napomene: en.napomene, pokazatelji, izvori, tipologija };
}

/**
 * Counties under their English names. The Croatian name stays in `naziv_hr`, so search
 * still finds "Splitsko-dalmatinska".
 * @param {Record<string, any>} zupanije
 * @param {any} en
 */
export function prevediZupanije(zupanije, en) {
  return Object.fromEntries(
    Object.entries(zupanije).map(([k, z]) => [k, { ...z, naziv: en.zupanije[k] ?? z.naziv, naziv_hr: z.naziv }]),
  );
}
