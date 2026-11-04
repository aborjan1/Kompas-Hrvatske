<script>
  // Charts tab of the info panel, for a selected county, city or municipality. Every
  // tema has its own: Novac the budget, Nabava the links, the others their series over
  // the years (GrafoviTeme).
  import { view } from '../state.js';
  import EuPozivi from './EuPozivi.svelte';
  import GrafoviTeme from './GrafoviTeme.svelte';
  import GrafVeza from './GrafVeza.svelte';
  import KamoIdeNovac from './KamoIdeNovac.svelte';
  import ProracunKrozGodine from './ProracunKrozGodine.svelte';
</script>

{#if $view.tema === 'novac'}
  <EuPozivi />
  <KamoIdeNovac />
  <ProracunKrozGodine />
{:else if $view.tema === 'nabava'}
  <GrafVeza />
  <GrafoviTeme />
{:else}
  <GrafoviTeme />
{/if}
