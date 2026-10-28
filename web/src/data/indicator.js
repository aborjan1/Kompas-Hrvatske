// Turns the current view (razina, tema, mjera) into numbers per area code. The map
// colours areas from this and the panels show its title and source, so the meaning
// of each tema lives in one place and the map never needs to know about temas.
//
// Stub: stays null until the data format (docs/format-podataka.md) is agreed with
// the data side. Until then the map keeps its own mock values.

import { derived } from 'svelte/store';
import { view } from '../state.js';

/**
 * @typedef {object} Indicator
 * @property {string} title Indicator name shown in the legend and panel.
 * @property {string} unit E.g. '€', '€ po stanovniku', '%'.
 * @property {number} godina Year of the data.
 * @property {string} izvor Dataset and publisher, shown under the map.
 * @property {Record<string, number>} values Keyed by area code (`sifra`).
 */

/** @type {import('svelte/store').Readable<Indicator | null>} */
export const indicator = derived(view, () => null);
