<script>
  // Charts column for a selected county, city or municipality on wide screens, shown only
  // when the area has charts. Narrower screens have the same charts in a tab of the info
  // panel (InfoPanel), so the two never render at the same time.
  import { view } from '../state.js';
  import { karticeGrafova } from '../data/grafovi.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';
  import { siroko } from './ekran.js';
  import { t } from '../jezik.js';
  import GrafoviKartice from './GrafoviKartice.svelte';

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));
  const vidljivo = $derived($siroko && Boolean(podrucje) && $karticeGrafova.length > 0);
</script>

{#if vidljivo}
  <aside class="kh-panel grafovi" aria-label="{t('Grafovi', 'Charts')}: {podrucje.naziv}">
    <GrafoviKartice>
      <p class="oznaka" style:color={TEME_POKAZATELJI[$view.tema].boje[3]}>{t('Grafovi', 'Charts')}</p>
      <h2>{podrucje.naziv}</h2>
    </GrafoviKartice>
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
