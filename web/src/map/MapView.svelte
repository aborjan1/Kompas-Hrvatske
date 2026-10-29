<script>
  import { onMount } from 'svelte';
  import { indicator } from '../data/indicator.js';
  import { selectArea, view } from '../state.js';
  import { COUNTY_BOUNDARIES_URL, CROATIA_BOUNDS, focusPadding } from './config.js';
  import { createCountyLayer, FILL_LAYER, SOURCE } from './countyLayer.js';
  import { createMap } from './createMap.js';
  import { formatNumber } from './format.js';
  import { addHoverTooltip } from './hover.js';
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
      const counties = createCountyLayer(map, await response.json());

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

      // createMap() already shows the whole country, so start from there.
      let focused = 'drzava/null';
      unsubscribeView = view.subscribe(({ razina, podrucje }) => {
        const key = `${razina}/${podrucje}`;
        if (key === focused) return;
        focused = key;
        // TODO(#23): a city or municipality needs the JLS boundaries.
        const bounds = razina === 'drzava' ? CROATIA_BOUNDS : counties.bounds(podrucje);
        if (bounds) map.fitBounds(bounds, { padding: focusPadding(container.clientWidth) });
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
  }
</style>
