<script>
  // Floating panels over the map. The layer itself lets pointer events through so the
  // map stays draggable between panels; only the panels catch clicks.
  import InfoPanel from './InfoPanel.svelte';
  import IzvorPodatka from './IzvorPodatka.svelte';
  import Pretraga from './Pretraga.svelte';
  import Putanja from './Putanja.svelte';
  import TemeBar from './TemeBar.svelte';
</script>

<div class="sloj">
  <div class="gore">
    <Putanja />
    <Pretraga />
  </div>
  <div class="desno"><InfoPanel /></div>
  <div class="dolje">
    <TemeBar />
    <IzvorPodatka />
  </div>
</div>

<style>
  .sloj {
    position: absolute;
    inset: 0;
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
    justify-items: center;
    gap: 6px;
    width: min(620px, calc(100% - 24px));
  }

  @media (max-width: 640px) {
    .desno {
      top: auto;
      right: 12px;
      bottom: 150px;
      width: calc(100% - 24px);
      max-height: 40%;
    }
  }
</style>
