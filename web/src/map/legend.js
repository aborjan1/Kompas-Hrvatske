// Choropleth legend as a Mapbox control, so it sits in the map's corner layout
// without the UI framework having to place it.

import { NO_DATA_COLOR } from './countyLayer.js';
import { formatNumber } from './format.js';
import './legend.css';

export class LegendControl {
  onAdd() {
    this.container = document.createElement('div');
    this.container.className = 'mapboxgl-ctrl kh-legend';
    this.container.hidden = true;
    return this.container;
  }

  onRemove() {
    this.container.remove();
  }

  /**
   * @param {{ title: string, opis?: string, format?: (value: number) => string,
   *   classes: { color: string, min: number, max: number }[], hasMissing: boolean }} legend
   *   `opis` is one plain-language sentence on what the number means, under the title.
   *   `format` turns a class bound into text with its unit ("563 mil. €").
   */
  update({ title, opis = '', format = formatNumber, classes, hasMissing }) {
    const range = (min, max) => (min === max ? format(min) : `${format(min)} – ${format(max)}`);
    const rows = classes.map((c) => row(c.color, range(c.min, c.max)));
    if (hasMissing) rows.push(row(NO_DATA_COLOR, 'nema podatka'));

    const head = [el('div', 'kh-legend__title', title)];
    if (opis) head.push(el('div', 'kh-legend__opis', opis));
    this.container.replaceChildren(...head, ...rows);
    this.container.hidden = classes.length === 0;
  }
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
