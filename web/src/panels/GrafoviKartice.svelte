<script module>
  // Open tab per tema. Out here so it outlives the component: the charts move between the
  // column and the info panel on resize, and the panels are rebuilt on a language change.
  /** @type {Record<string, string>} */
  const odabrane = $state({});
</script>

<script>
  // A tema's charts in tabs (src/data/grafovi.js says which the area has), used by the
  // charts column and the info panel's Grafovi tab. With one tab there is no tab row. Only
  // the open tab is rendered, so charts are drawn once they are visible.
  import { view } from '../state.js';
  import { karticeGrafova } from '../data/grafovi.js';
  import { t } from '../jezik.js';
  import EuPozivi from './EuPozivi.svelte';
  import GrafoviTeme from './GrafoviTeme.svelte';
  import GrafVeza from './GrafVeza.svelte';
  import KamoIdeNovac from './KamoIdeNovac.svelte';
  import Kartice from './Kartice.svelte';
  import ProracunKrozGodine from './ProracunKrozGodine.svelte';

  /** @type {{ children?: import('svelte').Snippet }} Title above the tabs. */
  let { children } = $props();

  const NAZIVI = {
    eu: t('EU pozivi', 'EU calls'),
    kamo: t('Kamo ide novac', 'Spending'),
    proracun: t('Kroz godine', 'Over the years'),
    veze: t('Veze', 'Links'),
    nizovi: t('Kroz godine', 'Over the years'),
  };

  const PREFIKS = 'graf-';

  const kartice = $derived($karticeGrafova.map((id) => ({ id, naziv: NAZIVI[id] })));
  const aktivna = $derived(
    $karticeGrafova.includes(odabrane[$view.tema]) ? odabrane[$view.tema] : $karticeGrafova[0],
  );
  const uKarticama = $derived(kartice.length > 1);
</script>

{#if children || uKarticama}
  <div class="glava">
    {@render children?.()}
    {#if uKarticama}
      <Kartice
        {kartice}
        {aktivna}
        oznaka={t('Grafovi', 'Charts')}
        prefiks={PREFIKS}
        onodaberi={(id) => (odabrane[$view.tema] = id)}
      />
    {/if}
  </div>
{/if}

{#key aktivna}
  <div
    class="ploca"
    role={uKarticama ? 'tabpanel' : undefined}
    id={uKarticama ? `ploca-${PREFIKS}${aktivna}` : undefined}
    aria-labelledby={uKarticama ? `kartica-${PREFIKS}${aktivna}` : undefined}
  >
    {#if aktivna === 'eu'}
      <EuPozivi />
    {:else if aktivna === 'kamo'}
      <KamoIdeNovac />
    {:else if aktivna === 'proracun'}
      <ProracunKrozGodine />
    {:else if aktivna === 'veze'}
      <GrafVeza />
    {:else}
      <GrafoviTeme />
    {/if}
  </div>
{/key}

<style>
  /* Directly under the info panel's own tabs, the spacing comes from the panel. */
  .glava > :global(.kartice:first-child) {
    margin-top: 0;
  }

  .ploca {
    padding-top: 12px;
    animation: kh-pojava 160ms ease-out both;
  }

  /* Each section brings its own top rule and spacing, which the first one under the
     tabs doesn't need. :global, because sections are other components. */
  .ploca > :global(:first-child) {
    margin-top: 0;
    padding-top: 0;
    border-top: 0;
  }

  @media (prefers-reduced-motion: reduce) {
    .ploca {
      animation: none;
    }
  }
</style>
