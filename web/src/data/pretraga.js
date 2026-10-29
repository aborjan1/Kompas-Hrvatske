// Name search over the 21 counties and 556 cities and municipalities, for the search
// box. Works without diacritics ("cakovec" finds Čakovec, "dakovo" and "djakovo" find
// Đakovo) and tolerates small typos. Pure functions over the loaded data.

import Fuse from 'fuse.js';

/**
 * @typedef {object} Rezultat
 * @property {'zupanija' | 'jls'} razina
 * @property {string} sifra
 * @property {string} naziv
 * @property {string} opis E.g. "Grad · Varaždinska županija", which tells apart the two Otoks.
 */

/**
 * Lower case without diacritics. NFD doesn't split đ (it's its own letter), so it is
 * mapped by hand: to "d" by default, to "dj" for the other common spelling.
 * @param {string} tekst
 * @param {'d' | 'dj'} [dj]
 */
export function normaliziraj(tekst, dj = 'd') {
  return tekst
    .toLowerCase()
    .replace(/đ/g, dj)
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '');
}

function varijante(naziv) {
  const d = normaliziraj(naziv, 'd');
  const dj = normaliziraj(naziv, 'dj');
  return d === dj ? [d] : [d, dj];
}

/**
 * @param {Record<string, import('./podaci.js').Podrucje> | null} zupanije
 * @param {Record<string, import('./podaci.js').Podrucje> | null} jls Null while still loading: counties only.
 * @returns {Fuse<Rezultat & { trazi: string[] }>}
 */
export function napraviIndeks(zupanije, jls) {
  const stavke = [];
  for (const z of Object.values(zupanije ?? {})) {
    stavke.push({ razina: 'zupanija', sifra: z.sifra, naziv: z.naziv, opis: 'Županija', trazi: varijante(z.naziv) });
  }
  for (const j of Object.values(jls ?? {})) {
    const vrsta = j.vrsta === 'grad' ? 'Grad' : 'Općina';
    const zupanija = zupanije?.[j.nadredeno]?.naziv;
    stavke.push({
      razina: 'jls',
      sifra: j.sifra,
      naziv: j.naziv,
      opis: zupanija ? `${vrsta} · ${zupanija}` : vrsta,
      trazi: varijante(j.naziv),
    });
  }
  return new Fuse(stavke, {
    keys: ['trazi'],
    includeScore: true,
    // Anywhere in the name ("zagreb" finds Grad Zagreb), with room for a typo or two.
    ignoreLocation: true,
    threshold: 0.3,
  });
}

/**
 * Best matches first: names that start with the query, then names with a word that
 * does, then Fuse's fuzzy score.
 * @param {ReturnType<typeof napraviIndeks>} indeks
 * @param {string} upit
 * @param {number} [najvise]
 * @returns {Rezultat[]}
 */
export function trazi(indeks, upit, najvise = 8) {
  const u = normaliziraj(upit.trim());
  if (u.length < 2) return [];
  return indeks
    .search(u)
    .map(({ item, score }) => {
      const pocinje = item.trazi.some((t) => t.startsWith(u));
      const rijec = item.trazi.some((t) => t.split(/[\s-]+/).some((w) => w.startsWith(u)));
      return { item, kazna: score - (pocinje ? 1 : 0) - (rijec ? 0.5 : 0) };
    })
    .sort((a, b) => a.kazna - b.kazna || a.item.naziv.localeCompare(b.item.naziv, 'hr'))
    .slice(0, najvise)
    .map(({ item: { razina, sifra, naziv, opis } }) => ({ razina, sifra, naziv, opis }));
}
