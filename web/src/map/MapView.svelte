<script>
  import { onMount } from 'svelte';
  import { COUNTY_BOUNDARIES_URL } from './config.js';
  import { createCountyLayer } from './countyLayer.js';
  import { createMap } from './createMap.js';
  import { mockIndicator } from './dev/mockIndicator.js';
  import { LegendControl } from './legend.js';

  let container;

  onMount(() => {
    const map = createMap(container);
    const legend = new LegendControl();
    map.addControl(legend, 'bottom-left');

    map.on('load', async () => {
      const geojson = await (await fetch(COUNTY_BOUNDARIES_URL)).json();
      const counties = createCountyLayer(map, geojson);

      // TODO: take the selected indicator from shared app state once it exists.
      const { title, unit, values } = mockIndicator;
      legend.update({ title, unit, ...counties.setValues(values) });
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
