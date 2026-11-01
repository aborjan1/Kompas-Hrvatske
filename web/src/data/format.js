// Number formatting for the panels, driven by `jedinica` and `decimale` from meta.json.
// Croatian conventions: 1.234.567,8 and a space before units, including %.

// Units that read better without a label ("3.871.833", not "3.871.833 osoba").
const SKRIVENE_JEDINICE = new Set(['osoba', 'broj']);

/**
 * @param {number} n
 * @returns {string} "1 projekt", "3 projekta", "12 projekata".
 */
export function brojProjekata(n) {
  const zadnja = n % 10;
  const zadnjeDvije = n % 100;
  const oblik =
    zadnja === 1 && zadnjeDvije !== 11 ? 'projekt'
    : zadnja >= 2 && zadnja <= 4 && (zadnjeDvije < 12 || zadnjeDvije > 14) ? 'projekta'
    : 'projekata';
  return `${broj(0).format(n)} ${oblik}`;
}

// Millions and billions: "563 mil.", "1,1 mlrd.", never "563,0 mil.".
const skraceno = new Intl.NumberFormat('hr-HR', { maximumFractionDigits: 1 });

const formati = new Map();
function broj(decimale) {
  if (!formati.has(decimale)) {
    formati.set(
      decimale,
      new Intl.NumberFormat('hr-HR', { minimumFractionDigits: decimale, maximumFractionDigits: decimale }),
    );
  }
  return formati.get(decimale);
}

/**
 * @param {number | null} value Raw value from the data files.
 * @param {string} jedinica Unit from meta.json, e.g. "EUR", "%", "EUR po stanovniku".
 * @param {number} decimale
 * @returns {string} E.g. "2,9 mlrd. €", "1.076 € po stanovniku", "3,3 %", or "nema podatka".
 */
export function formatVrijednost(value, jedinica, decimale) {
  if (value === null || !Number.isFinite(value)) return 'nema podatka';

  if (jedinica.startsWith('EUR')) {
    const ostatak = jedinica.slice(3); // " po stanovniku" or ""
    const iznos = Math.abs(value);
    if (iznos >= 1e9) return `${skraceno.format(value / 1e9)} mlrd. €${ostatak}`;
    if (iznos >= 1e6) return `${skraceno.format(value / 1e6)} mil. €${ostatak}`;
    return `${broj(decimale).format(value)} €${ostatak}`;
  }

  const tekst = broj(decimale).format(value);
  if (SKRIVENE_JEDINICE.has(jedinica)) return tekst;
  if (jedinica === 'godina') return `${tekst} god.`;
  return `${tekst} ${jedinica}`;
}
