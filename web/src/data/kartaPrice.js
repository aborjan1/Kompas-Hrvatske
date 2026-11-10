// The indicator a story scene colours the map by, in place of the tema's usual one
// (teme.js `karta`), so the map shows what the scene's sentence talks about. Set by the
// story player (src/stories/player.js) for each scene and cleared when the story ends;
// read by src/data/indicator.js. Null outside stories.

import { writable } from 'svelte/store';

/** @type {import('svelte/store').Writable<string | null>} */
const store = writable(null);

/** @type {import('svelte/store').Readable<string | null>} */
export const kartaPrice = { subscribe: store.subscribe };

/** @param {string | null} kljuc Indicator key from meta.json `pokazatelji`, or null. */
export function postaviKartuPrice(kljuc) {
  store.set(kljuc ?? null);
}
