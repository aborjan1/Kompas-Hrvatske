// "Preuzmi podatke": every indicator of the selected area as a CSV file, with unit, rank,
// period, source and licence on each row, so the numbers can be reused with their source.
// Croatian uses ";" and a decimal comma (what Excel expects with Croatian settings);
// English uses "," and a decimal point.

import { engleski, t } from '../jezik.js';
import { datumPreuzimanja } from './indicator.js';
import { normaliziraj } from './pretraga.js';

/** @param {string | null | undefined} licenca meta.json `licenca` in the current language. */
function dozvola(licenca) {
  if (!licenca) return '';
  if (!engleski()) return licenca;
  if (licenca.startsWith('Otvorena dozvola')) return 'Open Licence (data.gov.hr)';
  if (licenca.startsWith('Nije navedena')) return `Not stated ${licenca.slice('Nije navedena'.length).trim()}`;
  return licenca;
}

/**
 * @param {import('./podaci.js').Podaci} p
 * @param {import('../state.js').Razina} razina
 * @param {import('./podaci.js').Podrucje} podrucje
 * @returns {{ ime: string, sadrzaj: string }} File name and contents (with a BOM for Excel).
 */
export function csvPodrucja(p, razina, podrucje) {
  const en = engleski();
  const sep = en ? ',' : ';';
  const broj = (v) => (v === null || v === undefined || !Number.isFinite(v) ? '' : en ? String(v) : String(v).replace('.', ','));
  const polje = (v) => {
    const s = String(v ?? '');
    return s.includes(sep) || /["\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const ukupno =
    razina === 'zupanija' ? Object.keys(p.zupanije ?? {}).length
    : razina === 'jls' ? Object.keys(p.jls ?? {}).length
    : '';

  const zaglavlje = en
    ? ['code', 'area', 'indicator', 'name', 'value', 'unit', 'per_resident', 'per_resident_unit', 'rank', 'of', 'period', 'publisher', 'dataset', 'link', 'downloaded', 'licence']
    : ['sifra', 'podrucje', 'pokazatelj', 'naziv', 'vrijednost', 'jedinica', 'po_stanovniku', 'jedinica_po_stanovniku', 'rang', 'od', 'razdoblje', 'izdavatelj', 'skup_podataka', 'poveznica', 'preuzeto', 'dozvola'];
  const redovi = [zaglavlje];
  for (const [kljuc, pok] of Object.entries(p.meta.pokazatelji)) {
    if (!pok.razine.includes(razina)) continue;
    const vrijednost = podrucje.pokazatelji[kljuc];
    if (vrijednost === null || vrijednost === undefined) continue;
    const izvor = p.meta.izvori[pok.izvor];
    const dio = izvor?.dijelovi?.[0] ?? izvor;
    redovi.push([
      podrucje.sifra,
      podrucje.naziv,
      kljuc,
      pok.naziv,
      broj(vrijednost),
      pok.jedinica,
      pok.po_stanovniku ? broj(podrucje.po_stanovniku[kljuc]) : '',
      pok.po_stanovniku ? t(pok.po_stanovniku.jedinica, pok.po_stanovniku.jedinica.replace('EUR po stanovniku', 'EUR per resident').replace('na 1.000 stanovnika', 'per 1,000 residents')) : '',
      razina === 'drzava' ? '' : (podrucje.rang[kljuc] ?? ''),
      razina === 'drzava' ? '' : ukupno,
      pok.godina ?? '',
      izvor?.izdavatelj ?? '',
      izvor?.naziv ?? pok.izvor,
      izvor?.poveznica ?? dio?.poveznica ?? '',
      izvor ? (datumPreuzimanja(izvor) ?? '') : '',
      dozvola(izvor?.licenca ?? dio?.licenca),
    ]);
  }
  const sadrzaj = `﻿${redovi.map((r) => r.map(polje).join(sep)).join('\r\n')}\r\n`;
  const slug = normaliziraj(podrucje.naziv).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return { ime: `kompas-hrvatske-${slug}${en ? '-en' : ''}.csv`, sadrzaj };
}
