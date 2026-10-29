<script>
  // Floating panels over the map. The layer itself lets pointer events through so the
  // map stays draggable between panels; only the panels catch clicks.
  import DevOdabir from './dev/DevOdabir.svelte';
  import InfoPanel from './InfoPanel.svelte';
  import Putanja from './Putanja.svelte';
  import TemeBar from './TemeBar.svelte';
</script>

<div class="sloj">
  <div class="gore">
    <Putanja />
    {#if import.meta.env.DEV}<DevOdabir />{/if}
  </div>
  <div class="desno"><InfoPanel /></div>
  <div class="dolje"><TemeBar /></div>
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

  .dolje {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    max-width: calc(100% - 24px);
  }

  @media (max-width: 640px) {
    .desno {
      top: auto;
      right: 12px;
      bottom: 120px;
      width: calc(100% - 24px);
      max-height: 40%;
    }
  }
</style>
