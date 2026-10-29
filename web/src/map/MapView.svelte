<script>
  import { onMount } from 'svelte';
  import { indicator } from '../data/indicator.js';
  import { COUNTY_BOUNDARIES_URL } from './config.js';
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
