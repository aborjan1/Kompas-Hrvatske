<script>
  // Bottom bar: the four temas and the total / per-capita switch.
  import { MJERE, TEME, setMjera, setTema, view } from '../state.js';
  import { podaci } from '../data/podaci.js';
  import { indicator } from '../data/indicator.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  const MJERE_NAZIVI = { ukupno: 'Ukupno', 'po-stanovniku': 'Po stanovniku' };

  // The switch only means something when the mapped indicator has a per-capita value.
  const mjeraMoguca = $derived($indicator?.imaPoStanovniku ?? false);
</script>

<div class="kh-panel traka">
  <div class="grupa" role="group" aria-label="Tema">
    {#each TEME as tema}
      <button
        type="button"
        style:--boja-teme={TEME_POKAZATELJI[tema].boje[3]}
        aria-pressed={$view.tema === tema}
        onclick={() => setTema(tema)}
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
        onclick={() => setMjera(mjera)}
      >
        {MJERE_NAZIVI[mjera]}
      </button>
    {/each}
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

  button:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }
</style>
