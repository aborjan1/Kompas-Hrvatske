// Shared UI state. The map and the panels never call each other: both only read
// this store and change it through the functions below. Values match the URL,
// e.g. #/zupanija/05?tema=novac&mjera=po-stanovniku.
//
// Plain svelte/store (not runes) so the framework-agnostic map code in src/map/
// can subscribe from ordinary JS.

import { get, writable } from 'svelte/store';

/** @typedef {'drzava' | 'zupanija' | 'jls'} Razina */
/** @typedef {'ljudi' | 'novac' | 'porezi' | 'imovina'} Tema */
/** @typedef {'ukupno' | 'po-stanovniku'} Mjera */

/**
 * @typedef {object} View
 * @property {Razina} razina
 * @property {string | null} podrucje Area code (`sifra`) from the data files, treated
 *   as an opaque string; null at country level. For a JLS the parent county is looked
 *   up in the area list, not stored here.
 * @property {Tema} tema
 * @property {Mjera} mjera
 */

export const RAZINE = /** @type {const} */ (['drzava', 'zupanija', 'jls']);
export const TEME = /** @type {const} */ (['ljudi', 'novac', 'porezi', 'imovina']);
export const MJERE = /** @type {const} */ (['ukupno', 'po-stanovniku']);

/** @type {View} */
const INITIAL = { razina: 'drzava', podrucje: null, tema: 'novac', mjera: 'ukupno' };

const store = writable(INITIAL);

/**
 * Read-only view of the state. Every field change notifies every subscriber, so a
 * subscriber that only cares about some fields must compare them itself (the map
 * flies only when razina or podrucje changed).
 * @type {import('svelte/store').Readable<View>}
 */
export const view = { subscribe: store.subscribe };

/**
 * Select the area being viewed. Called by the map on click, by search on a result,
 * and by the breadcrumb ("Država" is `selectArea('drzava')`). Keeps tema and mjera.
 * @param {Razina} razina
 * @param {string | null} [podrucje] Area code; required for zupanija and jls, omitted for drzava.
 */
export function selectArea(razina, podrucje = null) {
  assertArea(razina, podrucje);
  set({ razina, podrucje });
}

/** @param {Tema} tema */
export function setTema(tema) {
  assertOneOf('tema', tema, TEME);
  set({ tema });
}

/** @param {Mjera} mjera */
export function setMjera(mjera) {
  assertOneOf('mjera', mjera, MJERE);
  set({ mjera });
}

/**
 * Set the whole view at once. Used by the URL sync (src/url.js) for a shared link and
 * for the browser's Back and Forward; everything else changes one part with the
 * functions above.
 * @param {View} next
 */
export function setView({ razina, podrucje = null, tema, mjera }) {
  assertArea(razina, podrucje);
  assertOneOf('tema', tema, TEME);
  assertOneOf('mjera', mjera, MJERE);
  set({ razina, podrucje, tema, mjera });
}

// svelte/store treats objects as always changed, so skip no-op writes here to
// avoid waking every subscriber when nothing changed.
/** @param {Partial<View>} patch */
function set(patch) {
  const current = get(store);
  const changed = Object.entries(patch).some(([key, value]) => current[key] !== value);
  if (changed) store.set({ ...current, ...patch });
}

function assertArea(razina, podrucje) {
  assertOneOf('razina', razina, RAZINE);
  if (razina === 'drzava' && podrucje !== null) {
    throw new Error(`razina 'drzava' takes no podrucje, got ${JSON.stringify(podrucje)}`);
  }
  if (razina !== 'drzava' && (typeof podrucje !== 'string' || podrucje === '')) {
    throw new Error(`razina '${razina}' needs podrucje as a string code, got ${JSON.stringify(podrucje)}`);
  }
}

function assertOneOf(name, value, allowed) {
  if (!allowed.includes(value)) {
    throw new Error(`Unknown ${name} ${JSON.stringify(value)}, expected one of: ${allowed.join(', ')}`);
  }
}
