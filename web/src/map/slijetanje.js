// Where the camera has landed, for whoever waits on it (stories show a scene's sentence
// only once the camera is there, src/stories/player.js). MapView reports every take-off
// and landing; the value is the landed view's key, null while the camera is in the air.

import { writable } from 'svelte/store';

/** @param {{ razina: string, podrucje?: string | null }} view */
export const kljucPogleda = ({ razina, podrucje }) => `${razina}/${podrucje ?? ''}`;

const store = writable(/** @type {string | null} */ (null));

export const sletjelo = { subscribe: store.subscribe };

export const javiPolijetanje = () => store.set(null);

/** @param {{ razina: string, podrucje?: string | null }} view The view the camera landed on. */
export const javiSletanje = (view) => store.set(kljucPogleda(view));
