// Choropleth legend as a MapLibre control, so it sits in the map's corner layout
// without the UI framework having to place it.

import { NO_DATA_COLOR } from './countyLayer.js';
import { formatNumber } from './format.js';
import './legend.css';

export class LegendControl {
  onAdd() {
    this.container = document.createElement('div');
    this.container.className = 'maplibregl-ctrl kh-legend';
    this.container.hidden = true;
    return this.container;
  }

  onRemove() {
    this.container.remove();
  }

  /**
   * @param {{ title: string, unit?: string,
   *   classes: { color: string, min: number, max: number }[], hasMissing: boolean }} legend
   */
  update({ title, unit, classes, hasMissing }) {
    const rows = classes.map((c) => row(c.color, range(c.min, c.max)));
    if (hasMissing) rows.push(row(NO_DATA_COLOR, 'nema podatka'));

    this.container.replaceChildren(
      el('div', 'kh-legend__title', unit ? `${title} (${unit})` : title),
      ...rows,
    );
    this.container.hidden = classes.length === 0;
  }
}

function range(min, max) {
  return min === max ? formatNumber(min) : `${formatNumber(min)} – ${formatNumber(max)}`;
}

function row(color, label) {
  const swatch = el('span', 'kh-legend__swatch');
  swatch.style.background = color;
  const r = el('div', 'kh-legend__row');
  r.append(swatch, label);
  return r;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text) node.textContent = text;
  return node;
}
