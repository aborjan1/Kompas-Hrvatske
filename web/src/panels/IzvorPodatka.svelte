<script>
  // Source and period of the indicator the map is coloured by, under the map. Follows
  // the map: county data for the country, city data inside a county.
  import { indicator } from '../data/indicator.js';

  const tekst = $derived($indicator ? `${$indicator.izvor} · ${$indicator.godina}` : '');
</script>

{#if $indicator}
  <p class="kh-panel izvor">
    <span class="oznaka">Izvor:</span>
    <span class="tekst" title={tekst}>{tekst}</span>
    {#if $indicator.poveznica}
      <a href={$indicator.poveznica} target="_blank" rel="noopener noreferrer">poveznica</a>
    {/if}
  </p>
{/if}

<style>
  .izvor {
    display: flex;
    align-items: baseline;
    gap: 6px;
    max-width: 100%;
    margin: 0;
    padding: 4px 10px;
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }

  .oznaka {
    flex: none;
    font-weight: 600;
  }

  /* Some dataset titles run to 150 characters; the full text is in the tooltip. */
  .tekst {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  a {
    flex: none;
    color: var(--kh-naglasak);
  }
</style>
