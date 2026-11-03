<script>
  // Charts over the years for the Ljudi, Porezi and Imovina temas (series in
  // src/data/nizovi.js). Novac has its own budget charts (KamoIdeNovac, ProracunKrozGodine).
  import { view } from '../state.js';
  import { SERIJE_TEME, ucitajNizove } from '../data/nizovi.js';
  import GrafNiz from './GrafNiz.svelte';

  $effect(() => ucitajNizove());

  const serije = $derived(SERIJE_TEME[$view.tema] ?? []);
</script>

{#each serije as sid (sid)}
  <GrafNiz {sid} />
{/each}
