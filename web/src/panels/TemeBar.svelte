<script>
  // Bottom bar: the four temas, the total / per-capita switch and the EU projects layer.
  // On phones the three groups fold into a menu behind one pill showing the current
  // choice, so they don't cover the map (styles in src/raspored.css).
  import { MJERE, TEME, setMjera, setTema, view } from '../state.js';
  import { euProjekti, prebaciEuProjekte } from '../data/euProjekti.js';
  import { podaci } from '../data/podaci.js';
  import { indicator } from '../data/indicator.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  const MJERE_NAZIVI = { ukupno: 'Ukupno', 'po-stanovniku': 'Po stanovniku' };

  // The switch only means something when the mapped indicator has a per-capita value.
  const mjeraMoguca = $derived($indicator?.imaPoStanovniku ?? false);

  const temaNaziv = $derived($podaci.meta?.teme[$view.tema] ?? $view.tema);
  const sazetak = $derived(
    [temaNaziv, MJERE_NAZIVI[mjeraMoguca ? $view.mjera : 'ukupno'], $euProjekti.prikazano && 'EU']
      .filter(Boolean)
      .join(' · '),
  );

  let otvoreno = $state(false);
  /** @type {HTMLElement | undefined} */
  let traka = $state();
  /** @type {HTMLButtonElement | undefined} */
  let pilula = $state();

  /** A pick in the phone menu closes it; on wider screens the menu is always shown. */
  function odaberi(radnja) {
    radnja();
    if (!otvoreno) return;
    otvoreno = false;
    pilula?.focus();
  }

  function onpointerdown(e) {
    if (otvoreno && !traka?.contains(e.target)) otvoreno = false;
  }

  function onkeydown(e) {
    if (otvoreno && e.key === 'Escape') {
      otvoreno = false;
      pilula?.focus();
    }
  }
</script>

<svelte:window {onpointerdown} {onkeydown} />

<div class="kh-panel traka" bind:this={traka}>
  <button
    type="button"
    class="pilula"
    style:--boja-teme={TEME_POKAZATELJI[$view.tema].boje[3]}
    aria-expanded={otvoreno}
    aria-controls="tema-izbornik"
    bind:this={pilula}
    onclick={() => (otvoreno = !otvoreno)}
  >
    {sazetak} <span aria-hidden="true">▾</span>
  </button>

  <div id="tema-izbornik" class="izbornik" class:otvoreno>
  <div class="grupa" role="group" aria-label="Tema">
    {#each TEME as tema}
      <button
        type="button"
        style:--boja-teme={TEME_POKAZATELJI[tema].boje[3]}
        aria-pressed={$view.tema === tema}
        onclick={() => odaberi(() => setTema(tema))}
      >
        {$podaci.meta?.teme[tema] ?? tema}
      </button>
    {/each}
  </div>

  <div
    class="grupa mjera"
    role="group"
    aria-label="Mjera"
    title={mjeraMoguca ? undefined : 'Ovaj pokazatelj nema vrijednost po stanovniku'}
  >
    {#each MJERE as mjera}
      <button
        type="button"
        aria-pressed={mjeraMoguca ? $view.mjera === mjera : mjera === 'ukupno'}
        disabled={!mjeraMoguca}
        onclick={() => odaberi(() => setMjera(mjera))}
      >
        {MJERE_NAZIVI[mjera]}
      </button>
    {/each}
  </div>

  <div class="grupa">
    <button
      type="button"
      class="eu"
      aria-pressed={$euProjekti.prikazano}
      aria-busy={$euProjekti.prikazano && !$euProjekti.poJls}
      title="Krugovi po gradu: koliko EU novca je dobio (2014.–2020.)"
      onclick={() => odaberi(prebaciEuProjekte)}
    >
      EU projekti
    </button>
  </div>
  </div>
</div>

<style>
  /* Never wider than the screen: on a phone the switch wraps under the temas. */
  .traka {
    box-sizing: border-box;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px 16px;
    max-width: 100%;
    padding: 8px;
  }

  /* The pill and the folding menu are for phones only (src/raspored.css). */
  .pilula {
    display: none;
  }

  .izbornik {
    display: contents;
  }

  .grupa {
    display: flex;
    gap: 2px;
    padding: 2px;
    border-radius: 8px;
    background: var(--kh-pozadina-blaga);
  }

  button {
    padding: 6px 12px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--kh-tekst);
    font: inherit;
    font-size: 14px;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
    background: rgba(0, 0, 0, 0.05);
  }

  button[aria-pressed='true'] {
    background: var(--boja-teme, var(--kh-naglasak));
    color: #fff;
  }

  /* EU flag colours, matching the circles on the map. */
  button.eu[aria-pressed='true'] {
    background: #003399;
    color: #ffcc00;
  }

  button.eu[aria-busy='true'] {
    opacity: 0.7;
    cursor: progress;
  }

  button:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }
</style>
