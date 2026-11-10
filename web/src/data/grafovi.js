// Which chart tabs the selected area has for the tema (GrafoviKartice.svelte). The charts
// column and the info panel's Grafovi tab both ask here, so neither opens empty. A tab
// counts as there until its data has loaded, so the row doesn't jump, and is gone if the
// data can't be loaded.

import { derived } from 'svelte/store';
import { view } from '../state.js';
import { euPozivi, ucitajEuPozive } from './euPozivi.js';
import { nabava, ucitajNabavu } from './nabava.js';
import { imaGrafove, nizovi, ucitajNizove } from './nizovi.js';
import { proracuni, ucitajProracune, zbrojFunkcija } from './proracuni.js';

/**
 * @template T
 * @param {{ podaci: T | null, greska: boolean }} izvor
 * @param {(podaci: T) => boolean} ima
 */
const dostupno = (izvor, ima) => (izvor.podaci ? ima(izvor.podaci) : !izvor.greska);

/**
 * Tab ids in order. Each test is the one its component uses to render nothing, so
 * EU calls and links stay even with an empty list: those say so in words.
 * @type {import('svelte/store').Readable<('eu' | 'kamo' | 'proracun' | 'veze' | 'nizovi')[]>}
 */
export const karticeGrafova = derived(
  [view, nizovi, proracuni, nabava, euPozivi],
  ([$view, $nizovi, $proracuni, $nabava, $euPozivi]) => {
    const { razina, tema, podrucje: sifra } = $view;
    if (razina === 'drzava') return [];
    const uNizovima = dostupno($nizovi, (n) => imaGrafove(n, tema, sifra));
    const kartice = {
      novac: [
        ['eu', dostupno($euPozivi, () => true)],
        ['kamo', dostupno($proracuni, (p) => zbrojFunkcija(p.podrucja[sifra]) > 0)],
        ['proracun', dostupno($proracuni, (p) => Boolean(p.podrucja[sifra]))],
      ],
      nabava: [
        ['veze', dostupno($nabava, (n) => Boolean(n.podrucja[sifra]))],
        ['nizovi', uNizovima],
      ],
    }[tema] ?? [['nizovi', uNizovima]];
    return kartice.filter(([, ima]) => ima).map(([id]) => id);
  },
);

/**
 * Loads what the tabs of a tema depend on, so they settle before any of them is opened.
 * @param {import('../state.js').Tema} tema
 */
export function ucitajGrafove(tema) {
  if (tema === 'novac') {
    ucitajEuPozive();
    ucitajProracune();
    return;
  }
  if (tema === 'nabava') ucitajNabavu();
  ucitajNizove();
}
