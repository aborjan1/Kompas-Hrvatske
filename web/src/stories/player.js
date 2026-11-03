// Plays a story like a short film. Starting one shows its title over the map while the
// panels step aside (html[data-kino], src/raspored.css) and the camera tilts in; then
// each scene goes:
//   odlazak  the map's colours fade out,
//   let      the scene sets the shared view and the camera flies there, slowly,
//   prikaz   once it has landed (src/map/slijetanje.js) the colours come back and the
//            scene's sentence appears (PricaKartica.svelte).
// MapView.svelte follows `reprodukcija` for the camera and the colours. Scenes replace
// the current history entry instead of adding one, and ending a story brings back the
// view and layer from before it, so Back after a story goes where it went before.

import { get, writable } from 'svelte/store';
import { setView, view } from '../state.js';
import { podaci, ucitajJls } from '../data/podaci.js';
import { euProjekti, prikaziEuProjekte } from '../data/euProjekti.js';
import { kljucPogleda, sletjelo } from '../map/slijetanje.js';
import { bezNovogZapisa } from '../url.js';
import { engleski, jezik, t } from '../jezik.js';
import { imaPodatke, rijesiScenu } from './scene.js';
import PRICE from './price.json';

/** @type {import('./scene.js').Prica[]} */
export const price = PRICE;

export const smanjenoKretanje =
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

// The title over the map at the start, while the camera tilts in.
const UVOD_MS = smanjenoKretanje ? 1500 : 2200;
// The colours fade out before the camera leaves (MapView, 300 ms).
const GASENJE_MS = smanjenoKretanje ? 0 : 320;
// A camera that never reports landing (an area without boundaries) doesn't hold the
// story up for longer than this.
const NAJDULJE_LETI_MS = 9000;

/**
 * Title and description of a story in the current language (`naslov_en`, `opis_en`).
 * @param {import('./scene.js').Prica} prica
 */
export function tekstPrice(prica) {
  const en = engleski();
  return { naslov: (en && prica.naslov_en) || prica.naslov, opis: (en && prica.opis_en) || prica.opis };
}

/** @param {import('./scene.js').Scena} scena The scene with its text in the current language (`tekst_en`). */
const uJeziku = (scena) => (engleski() && scena.tekst_en ? { ...scena, tekst: scena.tekst_en } : scena);

const bezPodataka = () => t('Za ovu scenu nema podataka.', 'There is no data for this scene.');

/**
 * @typedef {'uvod' | 'odlazak' | 'let' | 'prikaz'} Faza
 * @typedef {object} Reprodukcija
 * @property {import('./scene.js').Prica} prica
 * @property {number} indeks Current scene.
 * @property {Faza} faza
 * @property {string | null} tekst The scene's sentence, from `let` on.
 */

/** @type {import('svelte/store').Writable<Reprodukcija | null>} */
const store = writable(null);

/** The story being played, or null. */
export const reprodukcija = { subscribe: store.subscribe };

let prije = null;
// Bumped by every scene change and by the end, so a sequence still waiting (on the
// title, the data or the camera) stops at its next step.
let tok = 0;

/** @param {string} id */
export async function pokreni(id) {
  const prica = price.find((p) => p.id === id);
  if (!prica) return;
  if (!get(store)) prije = { view: get(view), eu: get(euProjekti).prikazano };
  if (prica.scene.some((s) => s.razina === 'jls')) ucitajJls();
  const moj = ++tok;
  // Before the store, so the map reads the full-screen frame when it reacts.
  document.documentElement.dataset.kino = '';
  store.set({ prica, indeks: 0, faza: 'uvod', tekst: null });
  await cekaj(UVOD_MS);
  if (moj === tok) prikazi(prica, 0);
}

export function dalje() {
  const r = get(store);
  if (r && r.faza !== 'uvod' && r.indeks < r.prica.scene.length - 1) prikazi(r.prica, r.indeks + 1);
}

export function natrag() {
  const r = get(store);
  if (r && r.faza !== 'uvod' && r.indeks > 0) prikazi(r.prica, r.indeks - 1);
}

/** @param {number} indeks */
export function idiNa(indeks) {
  const r = get(store);
  if (r && indeks >= 0 && indeks < r.prica.scene.length && indeks !== r.indeks) prikazi(r.prica, indeks);
}

/** Ends the story and brings back the view from before it. */
export function zavrsi() {
  tok++;
  if (!get(store)) return;
  delete document.documentElement.dataset.kino;
  store.set(null);
  if (prije) {
    const { view: v, eu } = prije;
    bezNovogZapisa(() => setView(v));
    prikaziEuProjekte(eu);
    prije = null;
  }
}

/**
 * @param {import('./scene.js').Prica} prica
 * @param {number} indeks
 */
async function prikazi(prica, indeks) {
  const moj = ++tok;
  const scena = uJeziku(prica.scene[indeks]);
  const bilo = get(store)?.faza;
  store.set({ prica, indeks, faza: 'odlazak', tekst: null });
  if (bilo === 'prikaz' || bilo === 'let') await cekaj(GASENJE_MS);
  if (moj !== tok) return;

  // A city scene may wait for jls.json the first time.
  const p = await dok(podaci, (p) => imaPodatke(p, scena));
  if (moj !== tok) return;
  const rijeseno = rijesiScenu(p, scena);
  const tekst = rijeseno?.tekst ?? bezPodataka();
  if (rijeseno) bezNovogZapisa(() => setView(rijeseno.view));
  store.set({ prica, indeks, faza: 'let', tekst });

  // Already there (the same area as the last scene) or once the camera lands.
  if (rijeseno) {
    const cilj = kljucPogleda(rijeseno.view);
    await dok(sletjelo, (k) => k === cilj, NAJDULJE_LETI_MS);
  }
  if (moj !== tok) return;
  prikaziEuProjekte(Boolean(scena.eu));
  store.set({ prica, indeks, faza: 'prikaz', tekst });
}

const cekaj = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Resolves with the store's value once `uvjet` holds for it, or after `najdulje` ms.
 * @template T
 * @param {import('svelte/store').Readable<T>} s
 * @param {(v: T) => boolean} uvjet
 * @param {number} [najdulje]
 * @returns {Promise<T>}
 */
function dok(s, uvjet, najdulje) {
  return new Promise((resolve) => {
    let gotovo = false;
    let odjava = null;
    let sat = 0;
    const kraj = (v) => {
      if (gotovo) return;
      gotovo = true;
      clearTimeout(sat);
      odjava?.();
      resolve(v);
    };
    if (najdulje !== undefined) sat = setTimeout(() => kraj(get(s)), najdulje);
    odjava = s.subscribe((v) => uvjet(v) && kraj(v));
    // Held already: subscribe called back before `odjava` was set.
    if (gotovo) odjava();
  });
}

// A language switch mid-story shows the scene's sentence in the new language, without
// flying again. (The title and controls follow on their own, PricaKartica.svelte.)
jezik.subscribe(() => {
  const r = get(store);
  if (!r || r.tekst === null) return;
  const rijeseno = rijesiScenu(get(podaci), uJeziku(r.prica.scene[r.indeks]));
  store.set({ ...r, tekst: rijeseno?.tekst ?? bezPodataka() });
});
