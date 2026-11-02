<script>
  // Floating panels over the map. The layer itself lets pointer events through so the
  // map stays draggable between panels; only the panels catch clicks.
  import GrafoviPanel from './GrafoviPanel.svelte';
  import InfoPanel from './InfoPanel.svelte';
  import IzvorPodatka from './IzvorPodatka.svelte';
  import Pretraga from './Pretraga.svelte';
  import PricaKartica from './PricaKartica.svelte';
  import Putanja from './Putanja.svelte';
  import TemeBar from './TemeBar.svelte';
  import { reprodukcija } from '../stories/player.js';
</script>

<div class="sloj" class:u-prici={$reprodukcija}>
  <div class="gore">
    <Putanja />
    <Pretraga />
  </div>
  <div class="lijevo"><GrafoviPanel /></div>
  <div class="desno"><InfoPanel /></div>
  <div class="dolje">
    <!-- A story sets the tema itself, so its card takes the tema bar's place. -->
    {#if $reprodukcija}<PricaKartica />{:else}<TemeBar />{/if}
    <IzvorPodatka />
  </div>
</div>

<style>
  .sloj {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    font-size: 14px;
    color: var(--kh-tekst);
  }

  .sloj :global(.kh-panel) {
    pointer-events: auto;
  }

  .gore {
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    display: grid;
    justify-items: center;
    gap: 8px;
    width: max-content;
    max-width: calc(100% - 24px);
  }

  /* Charts for the selected area (wide screens only, see ekran.js). Stops above the
     legend in the bottom-left corner. */
  .lijevo {
    position: absolute;
    top: 12px;
    left: 12px;
    width: 290px;
    max-height: calc(100% - 300px);
    overflow-y: auto;
    border-radius: 8px;
  }

  .u-prici .lijevo {
    display: none;
  }

  /* Leaves room for the map's zoom controls in the top-right corner. */
  .desno {
    position: absolute;
    top: 12px;
    right: 54px;
    width: min(290px, calc(100% - 78px));
    max-height: calc(100% - 100px);
    overflow-y: auto;
  }

  /* Fixed width so a long source line is cut with "…" instead of widening the bar. */
  .dolje {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    display: grid;
    /* minmax(0, …): the column must not grow to fit the unbroken source line, which
       would widen the whole page on a phone. */
    grid-template-columns: minmax(0, 1fr);
    justify-items: center;
    gap: 6px;
    width: min(620px, calc(100% - 24px));
  }

  /* Phones: everything stacks at the bottom, above the map's logo and attribution
     (the legend moves to the top left, see src/map/legend.css). */
  @media (max-width: 640px) {
    /* Full width up to the zoom buttons in the top-right corner. */
    .gore {
      left: 12px;
      right: 56px;
      grid-template-columns: minmax(0, 1fr);
      width: auto;
      max-width: none;
      transform: none;
    }

    .dolje {
      bottom: 40px;
    }

    /* During a story the card tells what is shown and the breadcrumb where, so the info
       panel steps aside and leaves the map visible. */
    .u-prici .desno {
      display: none;
    }

    .desno {
      top: auto;
      right: 12px;
      bottom: 180px;
      width: calc(100% - 24px);
      max-height: 40%;
    }
  }
</style>
