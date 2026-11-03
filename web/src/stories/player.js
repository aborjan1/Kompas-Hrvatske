// Plays a story: each scene sets the shared view (the map and panels follow it as
// usual) and, if it asks, the EU projects layer. Scenes replace the current history
// entry instead of adding one, and ending a story brings back the view and layer from
// before it, so Back after a story goes where it went before.

import { get, writable } from 'svelte/store';
import { setView, view } from '../state.js';
import { podaci, ucitajJls } from '../data/podaci.js';
import { euProjekti, prikaziEuProjekte } from '../data/euProjekti.js';
import { bezNovogZapisa } from '../url.js';
import { engleski, jezik, t } from '../jezik.js';
import { imaPodatke, rijesiScenu } from './scene.js';
import PRICE from './price.json';

/** @type {import('./scene.js').Prica[]} */
export const price = PRICE;

/**
 * Title and description of a story in the current language (`naslov_en`, `opis_en`).
 * @param {import('./scene.js').Prica} prica
 */
export function tekstPrice(prica) {
  const en = engleski();
  return { naslov: (en && prica.naslov_en) || prica.naslov, opis: (en && prica.opis_en) || prica.opis };
}

/**
 * @typedef {object} Reprodukcija
 * @property {import('./scene.js').Prica} prica
 * @property {number} indeks Current scene.
 * @property {string | null} tekst Null while the scene's data is still loading.
 */

/** @type {import('svelte/store').Writable<Reprodukcija | null>} */
const store = writable(null);

/** The story being played, or null. */
export const reprodukcija = { subscribe: store.subscribe };

let prije = null;
let cekanje = () => {};

/** @param {string} id */
export function pokreni(id) {
  const prica = price.find((p) => p.id === id);
  if (!prica) return;
  if (!get(store)) prije = { view: get(view), eu: get(euProjekti).prikazano };
  if (prica.scene.some((s) => s.razina === 'jls')) ucitajJls();
  prikazi(prica, 0);
}

export function dalje() {
  const r = get(store);
  if (r && r.indeks < r.prica.scene.length - 1) prikazi(r.prica, r.indeks + 1);
}

export function natrag() {
  const r = get(store);
  if (r && r.indeks > 0) prikazi(r.prica, r.indeks - 1);
}

/** Ends the story and brings back the view from before it. */
export function zavrsi() {
  cekanje();
  if (!get(store)) return;
  store.set(null);
  if (prije) {
    const { view: v, eu } = prije;
    bezNovogZapisa(() => setView(v));
    prikaziEuProjekte(eu);
    prije = null;
  }
}

function prikazi(prica, indeks) {
  cekanje();
  const izvorna = prica.scene[indeks];
  const scena = engleski() && izvorna.tekst_en ? { ...izvorna, tekst: izvorna.tekst_en } : izvorna;
  store.set({ prica, indeks, tekst: null });

  // Applies the scene once its data is there: at once, or when jls.json arrives for
  // the first city scene. `gotovo` makes sure it happens exactly once.
  let gotovo = false;
  let odjava = null;
  const primijeni = (p) => {
    if (gotovo || !imaPodatke(p, scena)) return;
    gotovo = true;
    odjava?.();
    const rijeseno = rijesiScenu(p, scena);
    if (rijeseno) bezNovogZapisa(() => setView(rijeseno.view));
    prikaziEuProjekte(Boolean(scena.eu));
    store.set({ prica, indeks, tekst: rijeseno?.tekst ?? t('Za ovu scenu nema podataka.', 'There is no data for this scene.') });
  };
  odjava = podaci.subscribe(primijeni);
  if (gotovo) odjava();
  cekanje = () => odjava();
}

// A language switch mid-story shows the same scene again, in the new language.
jezik.subscribe(() => {
  const r = get(store);
  if (r) prikazi(r.prica, r.indeks);
});
