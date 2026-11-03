// One plain-language sentence for the info panel, per tema and level, built from the
// numbers the panel shows. A clause whose number is missing is left out, so no view
// ends up with an empty sentence or "nema podatka" inside one. Ranks are order only
// (1 = largest), never "better" or "worse": that depends on the indicator.

import { nadjiPodrucje, ocitaj } from './podaci.js';
import { formatVrijednost } from './format.js';
import { engleski } from '../jezik.js';

/**
 * @param {import('./podaci.js').Podaci} p
 * @param {import('../state.js').View} v
 * @returns {string}
 */
export function napraviRecenicu(p, v) {
  const podrucje = nadjiPodrucje(p, v.razina, v.podrucje);
  if (!p.meta || !podrucje) return '';
  const h = pomocnik(p, podrucje, v);
  return (engleski() ? PREDLOSCI_EN : PREDLOSCI)[v.tema][v.razina](h, podrucje.naziv);
}

/**
 * Formatted values and ranks for one area, or null where the data has none.
 * @param {import('./podaci.js').Podaci} p
 * @param {import('./podaci.js').Podrucje} podrucje
 * @param {import('../state.js').View} v
 */
function pomocnik(p, podrucje, v) {
  const procitaj = (kljuc) => {
    const pokazatelj = p.meta.pokazatelji[kljuc];
    if (!pokazatelj?.razine.includes(v.razina)) return null;
    const o = ocitaj(podrucje, kljuc, pokazatelj, v.mjera);
    return o.value === null ? null : o;
  };
  const ukupno = v.razina === 'zupanija' ? Object.keys(p.zupanije ?? {}).length : Object.keys(p.jls ?? {}).length;
  return {
    /** Formatted value, e.g. "2,4 mlrd. €" or "438 € po stanovniku". */
    v(kljuc) {
      const o = procitaj(kljuc);
      return o && formatVrijednost(o.value, o.jedinica, o.decimale);
    },
    /** Whether the value is there and exactly zero. */
    nula(kljuc) {
      return procitaj(kljuc)?.value === 0;
    },
    /** " (7. od 21 županije)", or "" without a rank. */
    rang(kljuc) {
      const r = procitaj(kljuc)?.rang;
      if (!r || !ukupno || v.razina === 'drzava') return '';
      if (engleski()) {
        return ` (rank ${r} of ${ukupno} ${v.razina === 'zupanija' ? 'counties' : 'cities and municipalities'})`;
      }
      return ` (${r}. od ${ukupno} ${v.razina === 'zupanija' ? zupanija(ukupno) : 'gradova i općina'})`;
    },
  };
}

// "21 županije", "20 županija": after "od", numbers ending in 1 (but not 11) take the singular.
function zupanija(n) {
  return n % 10 === 1 && n % 100 !== 11 ? 'županije' : 'županija';
}

// Joins the clauses that have their numbers: "A, a b." or "A." or the fallback.
// In English: "A, and b." or "A.".
function spoji(...dijelovi) {
  const ima = dijelovi.filter(Boolean);
  const en = engleski();
  if (!ima.length) return en ? 'There is no data for this area in this theme.' : 'Za ovo područje nema podataka u ovoj temi.';
  const [prvi, ...ostali] = ima;
  const recenica = [prvi, ...ostali.map((d) => (en ? `and ${d}` : `a ${d}`))].join(', ');
  // Some units already end in a full stop ("45,1 god.").
  return recenica.endsWith('.') ? recenica : `${recenica}.`;
}

const ako = (vrijednost, tekst) => (vrijednost ? tekst : null);

/**
 * @type {Record<import('../state.js').Tema, Record<import('../state.js').Razina,
 *   (h: ReturnType<typeof pomocnik>, naziv: string) => string>>}
 */
const PREDLOSCI = {
  ljudi: {
    drzava: (h) =>
      spoji(
        ako(h.v('stanovnistvo'), `Hrvatska ima ${h.v('stanovnistvo')} stanovnika`),
        ako(h.v('prosjecna_neto_placa'), `prosječna plaća (na ruke) je ${h.v('prosjecna_neto_placa')}`),
      ),
    zupanija: (h, naziv) =>
      spoji(
        ako(h.v('stanovnistvo'), `${naziv} ima ${h.v('stanovnistvo')} stanovnika${h.rang('stanovnistvo')}`),
        ako(h.v('prosjecna_neto_placa'), `prosječna plaća je ${h.v('prosjecna_neto_placa')}${h.rang('prosjecna_neto_placa')}`),
      ),
    jls: (h, naziv) =>
      spoji(
        ako(h.v('stanovnistvo'), `${naziv} ima ${h.v('stanovnistvo')} stanovnika${h.rang('stanovnistvo')}`),
        ako(h.v('prosjecna_starost'), `prosječna dob je ${h.v('prosjecna_starost')}`),
      ),
  },
  novac: {
    drzava: (h) =>
      spoji(
        ako(h.v('bdp'), `Hrvatsko gospodarstvo vrijedi ${h.v('bdp')}`),
        ako(h.v('eu_2127_ugovoreno'), `iz EU fondova 2021.–2027. ugovoreno je ${h.v('eu_2127_ugovoreno')}`),
      ),
    zupanija: (h, naziv) =>
      spoji(
        ako(h.v('bruto_dodana_vrijednost'), `${naziv} zarađuje ${h.v('bruto_dodana_vrijednost')}${h.rang('bruto_dodana_vrijednost')}`),
        ako(h.v('eu_2127_ugovoreno'), `iz EU fondova 2021.–2027. ugovoreno je ${h.v('eu_2127_ugovoreno')}`),
      ),
    jls: (h, naziv) =>
      spoji(
        ako(h.v('lokalna_ulaganja'), `${naziv} ulaže ${h.v('lokalna_ulaganja')}${h.rang('lokalna_ulaganja')}`),
        ako(h.v('udio_pomoci_u_prihodima'), `${h.v('udio_pomoci_u_prihodima')} proračuna dolazi iz pomoći`),
      ),
  },
  porezi: {
    drzava: (h) => spoji(ako(h.v('porez_na_dohodak'), `Porez na plaće donio je ${h.v('porez_na_dohodak')}`)),
    zupanija: (h) =>
      spoji(
        ako(h.v('porez_na_dohodak'), `Porez na plaće donio je u županiji ${h.v('porez_na_dohodak')}${h.rang('porez_na_dohodak')}`),
      ),
    jls: (h) =>
      spoji(
        ako(
          h.v('stopa_poreza_dohodak_niza'),
          `Porez na plaću je ${h.v('stopa_poreza_dohodak_niza')}` +
            (h.v('stopa_poreza_dohodak_visa') ? ` (niža stopa) i ${h.v('stopa_poreza_dohodak_visa')} (viša)` : ''),
        ),
        ako(h.v('porez_na_nekretnine'), `porez na nekretnine je ${h.v('porez_na_nekretnine')}`),
      ),
  },
  imovina: {
    drzava: (h) =>
      spoji(
        ako(h.v('kupoprodaje_nekretnina'), `Broj prodanih nekretnina je ${h.v('kupoprodaje_nekretnina')}`),
        ako(h.v('pravne_osobe_aktivne'), `aktivnih tvrtki i udruga ${h.v('pravne_osobe_aktivne')}`),
      ),
    zupanija: (h) =>
      spoji(
        ako(h.v('kupoprodaje_nekretnina'), `Broj prodanih nekretnina je ${h.v('kupoprodaje_nekretnina')}${h.rang('kupoprodaje_nekretnina')}`),
        ako(h.v('porez_na_promet_nekretnina'), `porez od prodaje nekretnina donio je ${h.v('porez_na_promet_nekretnina')}`),
      ),
    // Below county level property is seen through the local budget (Ministry of Finance).
    jls: (h) =>
      spoji(
        ako(
          h.v('porez_na_promet_nekretnina'),
          `Porez od prodaje nekretnina donio je ${h.v('porez_na_promet_nekretnina')}${h.rang('porez_na_promet_nekretnina')}`,
        ),
        ako(h.v('prihodi_od_imovine'), `zakup i koncesije ${h.v('prihodi_od_imovine')}`),
      ),
  },
  nabava: {
    drzava: (h) =>
      spoji(
        ako(h.v('javna_nabava'), `Gradovi, općine i županije ugovorili su kroz javnu nabavu ${h.v('javna_nabava')} u pet godina`),
        ako(h.v('nabava_bez_objave'), `${h.v('nabava_bez_objave')} bez javnog poziva`),
      ),
    zupanija: (h) =>
      spoji(
        ako(h.v('javna_nabava'), `Lokalna uprava ugovorila je kroz javnu nabavu ${h.v('javna_nabava')}${h.rang('javna_nabava')}`),
        ako(h.v('nabava_najveci_dobavljac'), `najveći dobavljač dobio je ${h.v('nabava_najveci_dobavljac')} tog novca`),
      ),
    jls: (h, naziv) =>
      h.nula('javna_nabava')
        ? `${naziv} u pet godina nema ugovora u registru javne nabave (manje nabave ne moraju se ondje objavljivati).`
        : spoji(
            ako(h.v('javna_nabava'), `Kroz javnu nabavu ugovoreno je ${h.v('javna_nabava')}${h.rang('javna_nabava')}`),
            ako(h.v('nabava_najveci_dobavljac'), `najveći dobavljač dobio je ${h.v('nabava_najveci_dobavljac')} tog novca`),
          ),
  },
};

/** The same sentences in English (src/jezik.js). */
/** @type {typeof PREDLOSCI} */
const PREDLOSCI_EN = {
  ljudi: {
    drzava: (h) =>
      spoji(
        ako(h.v('stanovnistvo'), `Croatia has ${h.v('stanovnistvo')} residents`),
        ako(h.v('prosjecna_neto_placa'), `the average take-home salary is ${h.v('prosjecna_neto_placa')}`),
      ),
    zupanija: (h, naziv) =>
      spoji(
        ako(h.v('stanovnistvo'), `${naziv} has ${h.v('stanovnistvo')} residents${h.rang('stanovnistvo')}`),
        ako(h.v('prosjecna_neto_placa'), `the average salary is ${h.v('prosjecna_neto_placa')}${h.rang('prosjecna_neto_placa')}`),
      ),
    jls: (h, naziv) =>
      spoji(
        ako(h.v('stanovnistvo'), `${naziv} has ${h.v('stanovnistvo')} residents${h.rang('stanovnistvo')}`),
        ako(h.v('prosjecna_starost'), `the average age is ${h.v('prosjecna_starost')}`),
      ),
  },
  novac: {
    drzava: (h) =>
      spoji(
        ako(h.v('bdp'), `The Croatian economy is worth ${h.v('bdp')}`),
        ako(h.v('eu_2127_ugovoreno'), `${h.v('eu_2127_ugovoreno')} has been contracted from EU funds for 2021–2027`),
      ),
    zupanija: (h, naziv) =>
      spoji(
        ako(h.v('bruto_dodana_vrijednost'), `${naziv} earns ${h.v('bruto_dodana_vrijednost')}${h.rang('bruto_dodana_vrijednost')}`),
        ako(h.v('eu_2127_ugovoreno'), `${h.v('eu_2127_ugovoreno')} has been contracted from EU funds for 2021–2027`),
      ),
    jls: (h, naziv) =>
      spoji(
        ako(h.v('lokalna_ulaganja'), `${naziv} invests ${h.v('lokalna_ulaganja')}${h.rang('lokalna_ulaganja')}`),
        ako(h.v('udio_pomoci_u_prihodima'), `${h.v('udio_pomoci_u_prihodima')} of its budget comes from grants`),
      ),
  },
  porezi: {
    drzava: (h) => spoji(ako(h.v('porez_na_dohodak'), `Income tax brought in ${h.v('porez_na_dohodak')}`)),
    zupanija: (h) =>
      spoji(
        ako(h.v('porez_na_dohodak'), `Income tax brought in ${h.v('porez_na_dohodak')} in the county${h.rang('porez_na_dohodak')}`),
      ),
    jls: (h) =>
      spoji(
        ako(
          h.v('stopa_poreza_dohodak_niza'),
          `Income tax is ${h.v('stopa_poreza_dohodak_niza')}` +
            (h.v('stopa_poreza_dohodak_visa') ? ` (lower rate) and ${h.v('stopa_poreza_dohodak_visa')} (higher)` : ''),
        ),
        ako(h.v('porez_na_nekretnine'), `property tax is ${h.v('porez_na_nekretnine')}`),
      ),
  },
  imovina: {
    drzava: (h) =>
      spoji(
        ako(h.v('kupoprodaje_nekretnina'), `${h.v('kupoprodaje_nekretnina')} properties were sold`),
        ako(h.v('pravne_osobe_aktivne'), `there are ${h.v('pravne_osobe_aktivne')} active companies and associations`),
      ),
    zupanija: (h) =>
      spoji(
        ako(h.v('kupoprodaje_nekretnina'), `${h.v('kupoprodaje_nekretnina')} properties were sold${h.rang('kupoprodaje_nekretnina')}`),
        ako(h.v('porez_na_promet_nekretnina'), `the tax on property sales brought in ${h.v('porez_na_promet_nekretnina')}`),
      ),
    jls: (h) =>
      spoji(
        ako(
          h.v('porez_na_promet_nekretnina'),
          `The tax on property sales brought in ${h.v('porez_na_promet_nekretnina')}${h.rang('porez_na_promet_nekretnina')}`,
        ),
        ako(h.v('prihodi_od_imovine'), `leases and concessions ${h.v('prihodi_od_imovine')}`),
      ),
  },
  nabava: {
    drzava: (h) =>
      spoji(
        ako(h.v('javna_nabava'), `Cities, municipalities and counties contracted ${h.v('javna_nabava')} through public procurement in five years`),
        ako(h.v('nabava_bez_objave'), `${h.v('nabava_bez_objave')} without a public call`),
      ),
    zupanija: (h) =>
      spoji(
        ako(h.v('javna_nabava'), `Local government contracted ${h.v('javna_nabava')} through public procurement${h.rang('javna_nabava')}`),
        ako(h.v('nabava_najveci_dobavljac'), `the largest supplier received ${h.v('nabava_najveci_dobavljac')} of that money`),
      ),
    jls: (h, naziv) =>
      h.nula('javna_nabava')
        ? `${naziv} has no contracts in the public procurement register in five years (smaller purchases do not have to be published there).`
        : spoji(
            ako(h.v('javna_nabava'), `${h.v('javna_nabava')} was contracted through public procurement${h.rang('javna_nabava')}`),
            ako(h.v('nabava_najveci_dobavljac'), `the largest supplier received ${h.v('nabava_najveci_dobavljac')} of that money`),
          ),
  },
};
