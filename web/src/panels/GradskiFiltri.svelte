<script>
  // City view filters for Zagreb and Rijeka: which of the city's layers the map shows
  // over the satellite photo (src/map/cityLayers.js).
  import { view } from '../state.js';
  import { FILTRI, GRADOVI, prebaciFiltar, ukljuceniFiltri } from '../data/gradskiPrikaz.js';

  const grad = $derived($view.razina === 'jls' ? GRADOVI[$view.podrucje] : undefined);
</script>

{#if grad}
  <section class="grad">
    <h3>Gradski prikaz</h3>
    <div class="filtri" role="group" aria-label="Slojevi grada">
      {#each grad.filtri as filtar}
        <button
          type="button"
          style:--boja={FILTRI[filtar].boja}
          aria-pressed={$ukljuceniFiltri.has(filtar)}
          title={FILTRI[filtar].opis}
          onclick={() => prebaciFiltar(filtar)}
        >
          {FILTRI[filtar].naziv}
        </button>
      {/each}
    </div>
  </section>
{/if}

<style>
  .grad {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
  }

  h3 {
    margin: 0 0 8px;
    font-size: 13px;
    font-weight: 600;
  }

  .filtri {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  button {
    padding: 5px 10px;
    border: 1px solid var(--boja);
    border-radius: 999px;
    background: transparent;
    color: var(--boja);
    font: inherit;
    font-size: 13px;
    cursor: pointer;
    transition: background 150ms ease, color 150ms ease;
  }

  button[aria-pressed='true'] {
    background: var(--boja);
    color: #fff;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }

  @media (prefers-reduced-motion: reduce) {
    button {
      transition: none;
    }
  }

</style>
