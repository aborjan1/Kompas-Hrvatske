// Choropleth legend as a Mapbox control, so it sits in the map's corner layout
// without the UI framework having to place it.

import { NO_DATA_COLOR } from './countyLayer.js';
import { formatNumber } from './format.js';
import { t } from '../jezik.js';
import './legend.css';

export class LegendControl {
  onAdd() {
    this.container = document.createElement('div');
    this.container.className = 'mapboxgl-ctrl kh-legend';
    this.container.hidden = true;
    // Phones show a thin strip of the colours (legend.css); a tap opens the full legend.
    const telefon = matchMedia('(max-width: 640px)');
    const prebaci = () => {
      if (!telefon.matches) return;
      const otvorena = this.container.classList.toggle('kh-legend--otvorena');
      this.container.setAttribute('aria-expanded', String(otvorena));
    };
    this.container.addEventListener('click', prebaci);
    this.container.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      prebaci();
    });
    const ulogaGumba = () => {
      if (telefon.matches) {
        this.container.setAttribute('role', 'button');
        this.container.tabIndex = 0;
        this.container.setAttribute('aria-expanded', String(this.container.classList.contains('kh-legend--otvorena')));
        this.container.setAttribute('aria-label', t('Legenda', 'Legend'));
      } else {
        for (const a of ['role', 'tabindex', 'aria-expanded', 'aria-label']) this.container.removeAttribute(a);
      }
    };
    ulogaGumba();
    telefon.addEventListener('change', ulogaGumba);
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
    if (hasMissing) rows.push(row(NO_DATA_COLOR, t('nema podatka', 'no data')));

    const head = [el('div', 'kh-legend__title', title)];
    if (opis) head.push(el('div', 'kh-legend__opis', opis));
    this.container.replaceChildren(traka(classes, hasMissing, format), ...head, ...rows);
    this.container.hidden = classes.length === 0;
  }
}

// The phone strip: lowest value, the class colours side by side, highest value, and
// the "no data" colour when some areas lack one.
function traka(classes, hasMissing, format) {
  const strip = el('div', 'kh-legend__traka');
  if (classes.length === 0) return strip;
  const boje = el('span', 'kh-legend__boje');
  for (const c of classes) {
    const s = el('span', 'kh-legend__boja');
    s.style.background = c.color;
    boje.append(s);
  }
  strip.append(el('span', 'kh-legend__kraj', format(classes[0].min)), boje, el('span', 'kh-legend__kraj', format(classes.at(-1).max)));
  if (hasMissing) {
    const s = el('span', 'kh-legend__boja kh-legend__bez');
    s.style.background = NO_DATA_COLOR;
    s.title = t('nema podatka', 'no data');
    strip.append(s);
  }
  return strip;
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
