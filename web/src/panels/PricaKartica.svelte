<script>
  // The story being played, in place of the tema bar (the story sets the tema): the
  // scene's sentence and the controls. Arrow keys step through scenes, Esc ends the
  // story. "Automatski" steps on its own, for recording a video; it is not offered
  // when the system asks for reduced motion.
  import { dalje, natrag, reprodukcija, tekstPrice, zavrsi } from '../stories/player.js';
  import { t } from '../jezik.js';

  const TRAJANJE_SCENE = 7000; // ms, long enough to read the sentence after the camera lands

  const smanjenoKretanje =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  let automatski = $state(false);

  const r = $derived($reprodukcija);
  const ukupno = $derived(r?.prica.scene.length ?? 0);
  const naslov = $derived(r ? tekstPrice(r.prica).naslov : '');
  const zadnja = $derived(r ? r.indeks === ukupno - 1 : false);

  $effect(() => {
    if (!automatski || !r || r.tekst === null) return;
    if (zadnja) {
      automatski = false;
      return;
    }
    const t = setTimeout(dalje, TRAJANJE_SCENE);
    return () => clearTimeout(t);
  });

  $effect(() => {
    if (!r) automatski = false;
  });

  function onkeydown(e) {
    if (!r || e.defaultPrevented || e.target.closest?.('input, textarea, select')) return;
    if (e.key === 'ArrowRight') dalje();
    else if (e.key === 'ArrowLeft') natrag();
    else if (e.key === 'Escape') zavrsi();
    else return;
    e.preventDefault();
  }
</script>

<svelte:window {onkeydown} />

{#if r}
  <section class="kh-panel prica" aria-label="{t('Priča', 'Story')}: {naslov}">
    <div class="vrh">
      <p class="naslov">{naslov}</p>
      <span class="brojac" aria-label={t(`Scena ${r.indeks + 1} od ${ukupno}`, `Scene ${r.indeks + 1} of ${ukupno}`)}>{r.indeks + 1} / {ukupno}</span>
      <button
        type="button"
        class="zatvori"
        aria-label={t('Završi priču', 'End story')}
        title={t('Završi priču (Esc)', 'End story (Esc)')}
        onclick={zavrsi}
      >
        <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
          <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <p class="tekst" aria-live="polite">{r.tekst ?? t('Učitavanje…', 'Loading…')}</p>

    <div class="kontrole">
      <button type="button" onclick={natrag} disabled={r.indeks === 0}>‹ {t('Natrag', 'Back')}</button>
      {#if !smanjenoKretanje}
        <button type="button" aria-pressed={automatski} onclick={() => (automatski = !automatski)}>
          {t('Automatski', 'Auto-play')}
        </button>
      {/if}
      {#if zadnja}
        <button type="button" class="glavni" onclick={zavrsi}>{t('Završi', 'Finish')}</button>
      {:else}
        <button type="button" class="glavni" onclick={dalje}>{t('Dalje', 'Next')} ›</button>
      {/if}
    </div>
  </section>
{/if}

<style>
  .prica {
    box-sizing: border-box;
    width: 100%;
    padding: 10px 14px 12px;
  }

  .vrh {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .naslov {
    flex: 1;
    min-width: 0;
    margin: 0;
    overflow: hidden;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--kh-naglasak);
  }

  .brojac {
    flex: none;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
    color: var(--kh-tekst-blago);
  }

  .tekst {
    margin: 6px 0 10px;
    font-size: 15px;
    line-height: 1.45;
    color: var(--kh-tekst);
  }

  .kontrole {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
  }

  button {
    padding: 6px 12px;
    border: 0;
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    color: var(--kh-tekst);
    font: inherit;
    font-size: 14px;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
    background: #e4e3de;
  }

  button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  button[aria-pressed='true'],
  button.glavni {
    background: var(--kh-naglasak);
    color: #fff;
  }

  button.glavni:hover {
    background: #164c8f;
  }

  .zatvori {
    display: grid;
    flex: none;
    place-items: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 50%;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }
</style>
