import { engleski } from '../jezik.js';

// Which indicators (keys of meta.json `pokazatelji`) each tema shows. `karta` is the
// one the map colours, per coloured level (counties for the country, cities and
// municipalities inside a county); null means nothing to colour at that level.
// `panel` lists up to four for the info panel at each level. Keys an area level
// doesn't have (per meta.json `razine`) are skipped, so a list may name more than it shows.
// `boje` is the tema's map ramp: five classes, one hue, light → dark, OKLab lightness
// ~0.93 → ~0.35 in even steps. The fourth step doubles as the tema's accent colour.

// Everyday names for the indicators, shown on the map and in the panels instead of the
// official ones from meta.json (still shown on hover in the info panel). Keys missing
// here fall back to the official name.
/** @type {Record<string, string>} */
export const JEDNOSTAVNI_NAZIVI = {
  stanovnistvo: 'Broj stanovnika',
  prosjecna_starost: 'Prosječna dob stanovnika',
  prosjecna_neto_placa: 'Prosječna plaća (na ruke)',
  stopa_nezaposlenosti: 'Nezaposlenost',
  neto_dohodak: 'Ukupna primanja stanovnika',
  bdp: 'Vrijednost gospodarstva (BDP)',
  bruto_dodana_vrijednost: 'Koliko gospodarstvo zaradi',
  eu_2127_ugovoreno: 'Novac iz EU fondova (2021.–2027.)',
  hbor_krediti: 'Krediti iz EU fondova (HBOR)',
  inflacija: 'Rast cijena (inflacija)',
  lokalni_prihodi: 'Prihodi grada ili općine',
  lokalna_ulaganja: 'Ulaganja grada ili općine',
  udio_pomoci_u_prihodima: 'Dio proračuna koji dolazi iz pomoći',
  porez_na_dohodak: 'Plaćeni porez na plaće',
  stopa_poreza_dohodak_niza: 'Porez na plaću (niža stopa)',
  stopa_poreza_dohodak_visa: 'Porez na plaću (viša stopa)',
  porez_na_potrosnju: 'Porez na piće u kafićima i restoranima',
  porez_na_nekretnine: 'Porez na nekretnine',
  kupoprodaje_nekretnina: 'Prodane nekretnine',
  porez_na_promet_nekretnina: 'Porez od prodaje nekretnina',
  prihodi_od_imovine: 'Prihodi od zakupa i koncesija',
  javna_nabava: 'Ugovori javne nabave (5 godina)',
  nabava_najveci_dobavljac: 'Dio novca koji je dobila jedna tvrtka',
  nabava_bez_objave: 'Ugovori bez javnog poziva',
  pravne_osobe_aktivne: 'Aktivne tvrtke i udruge',
};

/** The same everyday names in English. */
/** @type {Record<string, string>} */
export const JEDNOSTAVNI_NAZIVI_EN = {
  stanovnistvo: 'Population',
  prosjecna_starost: 'Average age of residents',
  prosjecna_neto_placa: 'Average salary (take-home)',
  stopa_nezaposlenosti: 'Unemployment',
  neto_dohodak: 'Total income of residents',
  bdp: 'Size of the economy (GDP)',
  bruto_dodana_vrijednost: 'What the economy earns',
  eu_2127_ugovoreno: 'Money from EU funds (2021–2027)',
  hbor_krediti: 'Loans from EU funds (HBOR)',
  inflacija: 'Price growth (inflation)',
  lokalni_prihodi: 'City or municipality revenue',
  lokalna_ulaganja: 'City or municipality investment',
  udio_pomoci_u_prihodima: 'Share of the budget from grants',
  porez_na_dohodak: 'Income tax paid',
  stopa_poreza_dohodak_niza: 'Income tax (lower rate)',
  stopa_poreza_dohodak_visa: 'Income tax (higher rate)',
  porez_na_potrosnju: 'Tax on drinks in cafés and restaurants',
  porez_na_nekretnine: 'Property tax',
  kupoprodaje_nekretnina: 'Properties sold',
  porez_na_promet_nekretnina: 'Tax on property sales',
  prihodi_od_imovine: 'Revenue from leases and concessions',
  javna_nabava: 'Public procurement contracts (5 years)',
  nabava_najveci_dobavljac: 'Share won by a single company',
  nabava_bez_objave: 'Contracts without a public call',
  pravne_osobe_aktivne: 'Active companies and associations',
};

/**
 * Everyday name of an indicator in the current language, else its official name
 * (already English in English, src/data/prijevod.js).
 * @param {string} kljuc
 * @param {{ naziv: string }} pokazatelj
 */
export function jednostavniNaziv(kljuc, pokazatelj) {
  return (engleski() ? JEDNOSTAVNI_NAZIVI_EN : JEDNOSTAVNI_NAZIVI)[kljuc] ?? pokazatelj.naziv;
}

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
    karta: { zupanija: 'kupoprodaje_nekretnina', jls: 'porez_na_promet_nekretnina' },
    panel: {
      drzava: ['kupoprodaje_nekretnina', 'pravne_osobe_aktivne', 'porez_na_promet_nekretnina', 'prihodi_od_imovine'],
      zupanija: ['kupoprodaje_nekretnina', 'porez_na_promet_nekretnina', 'prihodi_od_imovine'],
      jls: ['porez_na_promet_nekretnina', 'prihodi_od_imovine'],
    },
  },
  nabava: {
    boje: ['#cfeeea', '#86cfc6', '#3aa79b', '#1d776d', '#0b4a43'],
    karta: { zupanija: 'javna_nabava', jls: 'javna_nabava' },
    panel: {
      drzava: ['javna_nabava', 'nabava_najveci_dobavljac', 'nabava_bez_objave'],
      zupanija: ['javna_nabava', 'nabava_najveci_dobavljac', 'nabava_bez_objave'],
      jls: ['javna_nabava', 'nabava_najveci_dobavljac', 'nabava_bez_objave'],
    },
  },
};
