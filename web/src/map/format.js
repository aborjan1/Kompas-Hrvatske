const numberFormat = new Intl.NumberFormat('hr-HR', { maximumFractionDigits: 1 });

export function formatNumber(value) {
  return numberFormat.format(value);
}
