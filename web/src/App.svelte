<script>
  import MapView from './map/MapView.svelte';
  import Paneli from './panels/Paneli.svelte';
</script>

<!-- Panels first, so Tab reaches the breadcrumb, search and panels before the map's
     own controls. They stay drawn above the map with a z-index (Paneli.svelte). -->
<Paneli />
<MapView />
