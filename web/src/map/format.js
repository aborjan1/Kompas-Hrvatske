import { lokal } from '../jezik.js';

export function formatNumber(value) {
  return new Intl.NumberFormat(lokal(), { maximumFractionDigits: 1 }).format(value);
}
