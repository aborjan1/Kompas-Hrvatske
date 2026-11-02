// City view (Zagreb and Rijeka): which of the four filters exist per city and which
// are switched on. Selecting the city on the map opens its view automatically; the
// panel switches the filters and the map draws them (src/map/cityLayers.js).

import { writable } from 'svelte/store';

/** @typedef {'ekonomska' | 'zone' | 'ulaganja' | 'imovina'} Filtar */

/** @type {Record<Filtar, { naziv: string, opis: string, boja: string }>} */
export const FILTRI = {
  ekonomska: {
    naziv: 'Ekonomska područja',
    opis: 'Gradske četvrti po udjelu gospodarske površine (2020.)',
    boja: '#b45309',
  },
  zone: {
    naziv: 'Poslovne zone',
    opis: 'Gospodarske zone iz prostornih planova (iscrtkano: neizgrađeno) i napuštene površine',
    boja: '#7c3aed',
  },
  ulaganja: {
    naziv: 'Javna ulaganja',
    opis: 'Planirana kapitalna ulaganja Grada 2023. i 2024., krug po iznosu',
    boja: '#0f766e',
  },
  imovina: {
    naziv: 'Gradska imovina',
    opis: 'Prazni gradski prostori i garaže, tržnice i gradska društva',
    boja: '#be185d',
  },
};

// JLS code → its folder in public/data/gradovi/ and the filters its data covers.
// Rijeka has no open district boundaries, zones or investments, only rented premises.
/** @type {Record<string, { mapa: string, filtri: Filtar[] }>} */
export const GRADOVI = {
  '01333': { mapa: 'zagreb', filtri: ['ekonomska', 'zone', 'ulaganja', 'imovina'] },
  '03735': { mapa: 'rijeka', filtri: ['imovina'] },
};

/** @type {import('svelte/store').Writable<Set<Filtar>>} */
const store = writable(new Set(['ulaganja', 'imovina']));

/** @type {import('svelte/store').Readable<Set<Filtar>>} */
export const ukljuceniFiltri = { subscribe: store.subscribe };

/** @param {Filtar} filtar */
export function prebaciFiltar(filtar) {
  store.update((s) => {
    const novi = new Set(s);
    if (!novi.delete(filtar)) novi.add(filtar);
    return novi;
  });
}
