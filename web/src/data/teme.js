// Which indicators (keys of meta.json `pokazatelji`) each tema shows. `karta` is the
// one the map colours, per coloured level (counties at country level, cities and
// municipalities inside a county); null means the map has nothing to colour.
// `panel` lists up to four for the info panel at each level. Keys an area level
// doesn't have (per meta.json `razine`) are skipped, so a list may name more than it shows.

/**
 * @type {Record<import('../state.js').Tema, {
 *   karta: Record<'zupanija' | 'jls', string | null>,
 *   panel: Record<import('../state.js').Razina, string[]>,
 * }>}
 */
export const TEME_POKAZATELJI = {
  ljudi: {
    karta: { zupanija: 'neto_dohodak', jls: 'neto_dohodak' },
    panel: {
      drzava: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      zupanija: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      jls: ['stanovnistvo', 'prosjecna_starost', 'neto_dohodak'],
    },
  },
  novac: {
    karta: { zupanija: 'bruto_dodana_vrijednost', jls: 'lokalna_ulaganja' },
    panel: {
      drzava: ['bdp', 'eu_2127_ugovoreno', 'hbor_krediti', 'inflacija'],
      zupanija: ['bruto_dodana_vrijednost', 'eu_2127_ugovoreno', 'lokalna_ulaganja', 'hbor_krediti'],
      jls: ['lokalni_prihodi', 'lokalna_ulaganja', 'eu_2127_ugovoreno', 'udio_pomoci_u_prihodima'],
    },
  },
  porezi: {
    karta: { zupanija: 'porez_na_dohodak', jls: 'stopa_poreza_dohodak_niza' },
    panel: {
      drzava: ['porez_na_dohodak'],
      zupanija: ['porez_na_dohodak', 'stopa_poreza_dohodak_niza', 'stopa_poreza_dohodak_visa'],
      jls: ['stopa_poreza_dohodak_niza', 'stopa_poreza_dohodak_visa', 'porez_na_potrosnju', 'porez_na_nekretnine'],
    },
  },
  imovina: {
    karta: { zupanija: 'kupoprodaje_nekretnina', jls: null },
    panel: {
      drzava: ['kupoprodaje_nekretnina', 'pravne_osobe_aktivne'],
      zupanija: ['kupoprodaje_nekretnina'],
      jls: [],
    },
  },
};
