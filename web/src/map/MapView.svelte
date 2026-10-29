<script>
  import { onMount } from 'svelte';
  import { indicator } from '../data/indicator.js';
  import { selectArea, view } from '../state.js';
  import {
    COUNTY_BOUNDARIES_URL,
    CROATIA_BOUNDS,
    FOCUS_PADDING,
    INTRO_DURATION,
  } from './config.js';
  import { createCountyLayer, FILL_LAYER, SOURCE } from './countyLayer.js';
  import { createMap, lockToCroatia } from './createMap.js';
  import { formatNumber } from './format.js';
  import { addHoverTooltip } from './hover.js';
  import { convexHull, simplifiedOutline } from './geometry.js';
  import { hidePlacesOutside } from './labels.js';
  import { LegendControl } from './legend.js';

  let container;

  onMount(() => {
    const map = createMap(container);
    const legend = new LegendControl();
    map.addControl(legend, 'bottom-left');

    /** @type {import('../data/indicator.js').Indicator | null} */
    let shown = null;
    let unsubscribe = () => {};
    let unsubscribeView = () => {};

    map.on('load', async () => {
      const response = await fetch(COUNTY_BOUNDARIES_URL);
      if (!response.ok) throw new Error(`${COUNTY_BOUNDARIES_URL}: HTTP ${response.status}`);
      const geojson = await response.json();
      const counties = createCountyLayer(map, geojson);
      const outline = simplifiedOutline(geojson);
      hidePlacesOutside(map, outline);

      unsubscribe = indicator.subscribe((ind) => {
        // Values per city/municipality belong to the JLS layer (phase 4); until then
        // the county colours stay as they were when the user enters a county.
        if (ind && ind.razina !== 'zupanija') return;
        shown = ind;
        const legendData = counties.setValues(ind?.values ?? {});
        legend.update({ title: ind?.title ?? '', unit: ind?.unit, ...legendData });
      });

      // The map only reports the click; the camera moves below, when the state changes,
      // so the breadcrumb, search and URL move it the same way.
      map.on('click', FILL_LAYER, (e) => selectArea('zupanija', e.features[0].properties.sifra));

      // Start the intro only once the globe is drawn, not over a blank sphere.
      await new Promise((resolve) => map.once('idle', resolve));

      // The first call is the intro: from the globe (createMap) straight down to the
      // current area, which is the whole country unless the app opened on a county.
      let focused = null;
      unsubscribeView = view.subscribe(({ razina, podrucje }) => {
        const key = `${razina}/${podrucje}`;
        if (key === focused) return;
        const intro = focused === null;
        focused = key;
        // TODO(#23): a city or municipality needs the JLS boundaries; until then the
        // intro lands on the whole country.
        const bounds =
          razina === 'zupanija' ? counties.bounds(podrucje)
          : razina === 'drzava' || intro ? CROATIA_BOUNDS
          : null;
        if (!bounds) return;

        // Listen first: under prefers-reduced-motion the intro is a jump, whose moveend
        // fires inside fitBounds().
        if (intro) {
          map.once('moveend', () => lockToCroatia(map, convexHull(outline.coordinates.flat(2))));
        }
        // Not `essential`, so MapLibre jumps instead of flying under prefers-reduced-motion.
        map.fitBounds(bounds, {
          padding: FOCUS_PADDING,
          pitch: map.getPitch(),
          ...(intro && { duration: INTRO_DURATION }),
        });
      });

      addHoverTooltip(map, {
        layerId: FILL_LAYER,
        source: SOURCE,
        describe: (f) => ({
          title: f.properties.naziv,
          detail: Number.isFinite(f.state.value)
            ? `${formatNumber(f.state.value)} ${shown.unit}`
            : 'nema podatka',
        }),
      });
    });

    return () => {
      unsubscribe();
      unsubscribeView();
      map.remove();
    };
  });
</script>

<div class="map" bind:this={container}></div>

<style>
  .map {
    position: absolute;
    inset: 0;
    /* Space behind the globe. */
    background: #0b1222;
  }
</style>
