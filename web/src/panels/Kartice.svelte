<script>
  // Tabs of the info panel. Arrow keys, Home and End move between them and open the tab
  // right away; only the open tab is in the Tab order, as the ARIA tabs pattern asks.
  import { t } from '../jezik.js';

  /** @type {{ kartice: { id: string, naziv: string }[], aktivna: string,
   *   onodaberi: (id: string) => void }} */
  let { kartice, aktivna, onodaberi } = $props();

  /** @type {HTMLElement | undefined} */
  let popis = $state();

  function odaberi(id) {
    onodaberi(id);
    popis?.querySelector(`#kartica-${id}`)?.focus();
  }

  function onkeydown(e) {
    const i = kartice.findIndex((k) => k.id === aktivna);
    const zadnji = kartice.length - 1;
    const novi = {
      ArrowRight: i === zadnji ? 0 : i + 1,
      ArrowLeft: i === 0 ? zadnji : i - 1,
      Home: 0,
      End: zadnji,
    }[e.key];
    if (novi === undefined) return;
    e.preventDefault();
    odaberi(kartice[novi].id);
  }
</script>

<div class="kartice" role="tablist" aria-label={t('Podaci o području', 'Area data')} bind:this={popis}>
  {#each kartice as k (k.id)}
    <button
      type="button"
      role="tab"
      id="kartica-{k.id}"
      aria-selected={k.id === aktivna}
      aria-controls={k.id === aktivna ? `ploca-${k.id}` : undefined}
      tabindex={k.id === aktivna ? 0 : -1}
      onclick={() => onodaberi(k.id)}
      {onkeydown}
    >
      {k.naziv}
    </button>
  {/each}
</div>

<style>
  .kartice {
    display: flex;
    flex: 0 0 100%;
    gap: 2px;
    margin-top: 8px;
    border-bottom: 1px solid var(--kh-rub);
  }

  button {
    flex: 1 1 0;
    min-width: 0;
    min-height: 36px;
    margin-bottom: -1px;
    padding: 6px 4px;
    border: 0;
    border-bottom: 2px solid transparent;
    background: none;
    color: var(--kh-tekst-blago);
    font: inherit;
    font-size: 13px;
    cursor: pointer;
    transition: color 150ms ease, border-color 150ms ease;
  }

  button:hover {
    color: var(--kh-tekst);
  }

  button[aria-selected='true'] {
    border-bottom-color: var(--kh-naglasak);
    color: var(--kh-tekst);
    font-weight: 600;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: -2px;
    border-radius: 4px;
  }

  @media (prefers-reduced-motion: reduce) {
    button {
      transition: none;
    }
  }
</style>
