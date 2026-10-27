<script>
  import { onMount } from 'svelte';
  import { createMap } from './createMap.js';

  let container;

  onMount(() => {
    const map = createMap(container);
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
