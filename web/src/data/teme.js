// Which indicators (keys of meta.json `pokazatelji`) each tema shows. `karta` is the
// one the map colours; `panel` lists up to four for the info panel at each level.
// Keys an area level doesn't have (per meta.json `razine`) are skipped, so a list may
// name more than it shows.

/** @type {Record<import('../state.js').Tema, { karta: string, panel: Record<import('../state.js').Razina, string[]> }>} */
export const TEME_POKAZATELJI = {
  ljudi: {
    karta: 'neto_dohodak',
    panel: {
      drzava: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      zupanija: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      jls: ['stanovnistvo', 'prosjecna_starost', 'neto_dohodak'],
    },
  },
  novac: {
    karta: 'bruto_dodana_vrijednost',
    panel: {
      drzava: ['bdp', 'eu_ugovoreno', 'hbor_krediti', 'inflacija'],
      zupanija: ['bruto_dodana_vrijednost', 'eu_ugovoreno', 'eu_projekti', 'hbor_krediti'],
      jls: [],
    },
  },
  porezi: {
    karta: 'porez_na_dohodak',
    panel: {
      drzava: ['porez_na_dohodak'],
      zupanija: ['porez_na_dohodak'],
      jls: ['porez_na_dohodak'],
    },
  },
  imovina: {
    karta: 'kupoprodaje_nekretnina',
    panel: {
      drzava: ['kupoprodaje_nekretnina', 'pravne_osobe_aktivne'],
      zupanija: ['kupoprodaje_nekretnina'],
      jls: [],
    },
  },
};
