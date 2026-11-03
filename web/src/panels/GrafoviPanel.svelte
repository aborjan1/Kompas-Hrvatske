<script>
  // Charts panel in the left column, for a selected county, city or municipality on
  // wide screens. Narrower screens show the same charts in the info panel (InfoPanel),
  // so this panel and that spot never render at the same time.
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';
  import { siroko } from './ekran.js';
  import GrafoviTeme from './GrafoviTeme.svelte';
  import KamoIdeNovac from './KamoIdeNovac.svelte';
  import ProracunKrozGodine from './ProracunKrozGodine.svelte';

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));
  // Every tema has charts for counties, cities and municipalities: Novac its budget,
  // the others their series over the years (GrafoviTeme).
  const vidljivo = $derived($siroko && $view.razina !== 'drzava' && Boolean(podrucje));
</script>

{#if vidljivo}
  <aside class="kh-panel grafovi" aria-label="Grafovi: {podrucje.naziv}">
    <p class="oznaka" style:color={TEME_POKAZATELJI[$view.tema].boje[3]}>Grafovi</p>
    <h2>{podrucje.naziv}</h2>
    {#if $view.tema === 'novac'}
      <KamoIdeNovac />
      <ProracunKrozGodine />
    {:else}
      <GrafoviTeme />
    {/if}
  </aside>
{/if}

<style>
  .grafovi {
    padding: 14px 16px;
  }

  .oznaka {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  h2 {
    margin: 2px 0 0;
    font-size: 16px;
    line-height: 1.25;
    color: var(--kh-tekst);
  }
</style>
