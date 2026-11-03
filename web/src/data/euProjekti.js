// EU projects (OPKK 2014.–2020., tocke/eu-projekti.geojson) summed per city or
// municipality. The file places every project at its town rather than its address,
// so one circle per JLS is what the data can honestly show. Loaded on first use
// (about 3.6 MB), since most visits never switch the layer on.

import { get, writable } from 'svelte/store';
import { t } from '../jezik.js';

const ADRESA = `${import.meta.env.BASE_URL}data/tocke/eu-projekti.geojson`;
const NAJVECIH = 5;

/**
 * @typedef {object} EuProjekt
 * @property {string} naziv
 * @property {string} korisnik
 * @property {number} esif_eur EU share of the project.
 */

/**
 * @typedef {object} EuJls
 * @property {string} sifra JLS code.
 * @property {string} mjesto
 * @property {[number, number]} polozaj Where the projects sit (the town).
 * @property {number} broj Number of projects.
 * @property {number} esif_eur Sum of the EU share.
 * @property {EuProjekt[]} najveci The largest projects by EU share, at most five.
 */

/**
 * @typedef {object} EuProjekti
 * @property {boolean} prikazano Whether the layer is switched on.
 * @property {Record<string, EuJls> | null} poJls Null until the file has loaded.
 * @property {string | null} presjek Date of the data, e.g. "31.05.2023".
 * @property {string | null} greska
 */

/** @type {import('svelte/store').Writable<EuProjekti>} */
const store = writable({ prikazano: false, poJls: null, presjek: null, greska: null });

/** @type {import('svelte/store').Readable<EuProjekti>} */
export const euProjekti = { subscribe: store.subscribe };

let zatrazeno = false;

/** @param {boolean} prikazano */
export function prikaziEuProjekte(prikazano) {
  store.update((s) => ({ ...s, prikazano }));
  if (!prikazano || zatrazeno) return;
  zatrazeno = true;
  fetch(ADRESA)
    .then((odgovor) => {
      if (!odgovor.ok) throw new Error(`eu-projekti.geojson: HTTP ${odgovor.status}`);
      return odgovor.json();
    })
    .then((geojson) => store.update((s) => ({ ...s, poJls: zbroji(geojson), presjek: geojson.presjek })))
    .catch((error) => {
      console.error(error);
      zatrazeno = false;
      store.update((s) => ({ ...s, greska: t('EU projekti se nisu učitali.', 'EU projects did not load.') }));
    });
}

export function prebaciEuProjekte() {
  prikaziEuProjekte(!get(store).prikazano);
}

/** @param {GeoJSON.FeatureCollection<GeoJSON.Point>} geojson */
function zbroji(geojson) {
  /** @type {Record<string, EuJls & { polozaji: Map<string, number> }>} */
  const poJls = {};
  for (const { geometry, properties: p } of geojson.features) {
    // A handful of projects lie at sea, outside every JLS.
    if (!p.jls) continue;
    const j = (poJls[p.jls] ??= {
      sifra: p.jls,
      mjesto: p.mjesto,
      polozaj: /** @type {[number, number]} */ (geometry.coordinates),
      broj: 0,
      esif_eur: 0,
      najveci: [],
      polozaji: new Map(),
    });
    j.broj++;
    j.esif_eur += p.esif_eur ?? 0;
    j.najveci.push({ naziv: p.naziv, korisnik: p.korisnik, esif_eur: p.esif_eur ?? 0 });
    const kljuc = geometry.coordinates.join();
    j.polozaji.set(kljuc, (j.polozaji.get(kljuc) ?? 0) + 1);
  }
  for (const j of Object.values(poJls)) {
    // Where most of its projects sit, which is the town itself.
    const [najcesci] = [...j.polozaji].sort((a, b) => b[1] - a[1])[0];
    j.polozaj = /** @type {[number, number]} */ (najcesci.split(',').map(Number));
    j.najveci = j.najveci.sort((a, b) => b.esif_eur - a.esif_eur).slice(0, NAJVECIH);
    delete j.polozaji;
  }
  return /** @type {Record<string, EuJls>} */ (poJls);
}
