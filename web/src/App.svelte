<script>
  import MapView from './map/MapView.svelte';
  import Paneli from './panels/Paneli.svelte';
  import PricaKartica from './panels/PricaKartica.svelte';
  import { jezik } from './jezik.js';
</script>

<!-- Panels first, so Tab reaches the breadcrumb, search and panels before the map's
     own controls. They stay drawn above the map with a z-index (Paneli.svelte), and a
     playing story above them (PricaKartica.svelte). -->
<!-- Rebuilt when the language changes (src/jezik.js), so every text is redrawn; the map
     stays and follows the language itself. -->
{#key $jezik}
  <Paneli />
  <PricaKartica />
{/key}
<MapView />
