// Which indicators (keys of meta.json `pokazatelji`) each tema shows. `karta` is the
// one the map colours, per coloured level (counties for the country, cities and
// municipalities inside a county); null means nothing to colour at that level.
// `panel` lists up to four for the info panel at each level. Keys an area level
// doesn't have (per meta.json `razine`) are skipped, so a list may name more than it shows.
// `boje` is the tema's map ramp: five classes, one hue, light → dark, OKLab lightness
// ~0.93 → ~0.35 in even steps. The fourth step doubles as the tema's accent colour.

/**
 * @type {Record<import('../state.js').Tema, {
 *   boje: string[],
 *   karta: Record<'zupanija' | 'jls', string | null>,
 *   panel: Record<import('../state.js').Razina, string[]>,
 * }>}
 */
export const TEME_POKAZATELJI = {
  ljudi: {
    boje: ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'],
    karta: { zupanija: 'neto_dohodak', jls: 'neto_dohodak' },
    panel: {
      drzava: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      zupanija: ['stanovnistvo', 'prosjecna_neto_placa', 'stopa_nezaposlenosti', 'neto_dohodak'],
      jls: ['stanovnistvo', 'prosjecna_starost', 'neto_dohodak'],
    },
  },
  novac: {
    boje: ['#dcf1d3', '#9fd38d', '#5aad4e', '#2b7f2e', '#0f5219'],
    karta: { zupanija: 'bruto_dodana_vrijednost', jls: 'lokalna_ulaganja' },
    panel: {
      drzava: ['bdp', 'eu_2127_ugovoreno', 'hbor_krediti', 'inflacija'],
      zupanija: ['bruto_dodana_vrijednost', 'eu_2127_ugovoreno', 'lokalna_ulaganja', 'hbor_krediti'],
      jls: ['lokalni_prihodi', 'lokalna_ulaganja', 'eu_2127_ugovoreno', 'udio_pomoci_u_prihodima'],
    },
  },
  porezi: {
    boje: ['#fde0c8', '#f5a670', '#e4692f', '#ad4113', '#6f2308'],
    karta: { zupanija: 'porez_na_dohodak', jls: 'stopa_poreza_dohodak_niza' },
    panel: {
      drzava: ['porez_na_dohodak'],
      zupanija: ['porez_na_dohodak', 'stopa_poreza_dohodak_niza', 'stopa_poreza_dohodak_visa'],
      jls: ['stopa_poreza_dohodak_niza', 'stopa_poreza_dohodak_visa', 'porez_na_potrosnju', 'porez_na_nekretnine'],
    },
  },
  imovina: {
    boje: ['#e7e2fa', '#b8acf0', '#8a78e2', '#5d48bd', '#34257f'],
    karta: { zupanija: 'kupoprodaje_nekretnina', jls: null },
    panel: {
      drzava: ['kupoprodaje_nekretnina', 'pravne_osobe_aktivne'],
      zupanija: ['kupoprodaje_nekretnina'],
      jls: [],
    },
  },
};
