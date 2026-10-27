<script>
  import { onMount } from 'svelte';
  import { COUNTY_BOUNDARIES_URL } from './config.js';
  import { createCountyLayer, FILL_LAYER, SOURCE } from './countyLayer.js';
  import { createMap } from './createMap.js';
  import { mockIndicator } from './dev/mockIndicator.js';
  import { formatNumber } from './format.js';
  import { addHoverTooltip } from './hover.js';
  import { LegendControl } from './legend.js';

  let container;

  onMount(() => {
    const map = createMap(container);
    const legend = new LegendControl();
    map.addControl(legend, 'bottom-left');

    map.on('load', async () => {
      const geojson = await (await fetch(COUNTY_BOUNDARIES_URL)).json();
      const counties = createCountyLayer(map, geojson);

      // TODO(Rafael): waiting on the `indicator` store (web/src/data/indicator.js).
      // Subscribe to it and call setValues() + legend.update() whenever it changes.
      const indicator = mockIndicator;
      legend.update({ ...indicator, ...counties.setValues(indicator.values) });

      addHoverTooltip(map, {
        layerId: FILL_LAYER,
        source: SOURCE,
        describe: (f) => ({
          title: f.properties.naziv,
          detail: Number.isFinite(f.state.value)
            ? `${formatNumber(f.state.value)} ${indicator.unit}`
            : 'nema podatka',
        }),
      });
    });

    return () => map.remove();
  });
</script>

<div class="map" bind:this={container}></div>

<style>
  .map {
    position: absolute;
    inset: 0;
  }
</style>
