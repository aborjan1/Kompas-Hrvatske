// One plain-language sentence for the info panel, per tema and level, built from the
// numbers the panel shows. A clause whose number is missing is left out, so no view
// ends up with an empty sentence or "nema podatka" inside one. Ranks are order only
// (1 = largest), never "better" or "worse": that depends on the indicator.

import { nadjiPodrucje, ocitaj } from './podaci.js';
import { formatVrijednost } from './format.js';

/**
 * @param {import('./podaci.js').Podaci} p
 * @param {import('../state.js').View} v
 * @returns {string}
 */
export function napraviRecenicu(p, v) {
  const podrucje = nadjiPodrucje(p, v.razina, v.podrucje);
  if (!p.meta || !podrucje) return '';
  const h = pomocnik(p, podrucje, v);
  return PREDLOSCI[v.tema][v.razina](h, podrucje.naziv);
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
    /** " (7. od 21 županije)", or "" without a rank. */
    rang(kljuc) {
      const r = procitaj(kljuc)?.rang;
      if (!r || !ukupno || v.razina === 'drzava') return '';
      return ` (${r}. od ${ukupno} ${v.razina === 'zupanija' ? zupanija(ukupno) : 'gradova i općina'})`;
    },
  };
}

// "21 županije", "20 županija": after "od", numbers ending in 1 (but not 11) take the singular.
function zupanija(n) {
  return n % 10 === 1 && n % 100 !== 11 ? 'županije' : 'županija';
}

// Joins the clauses that have their numbers: "A, a b." or "A." or the fallback.
function spoji(...dijelovi) {
  const ima = dijelovi.filter(Boolean);
  if (!ima.length) return 'Za ovo područje nema podataka u ovoj temi.';
  const [prvi, ...ostali] = ima;
  const recenica = [prvi, ...ostali.map((d) => `a ${d}`)].join(', ');
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
};
