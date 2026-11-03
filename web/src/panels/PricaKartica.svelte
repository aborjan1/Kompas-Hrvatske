<script>
  // The story being played, over the full-screen map (html[data-kino], raspored.css):
  // first its title, then each scene's sentence in a speech bubble once the camera has
  // landed (stories/player.js), with the controls under it. The story plays on its
  // own: a scene stays long enough to read its sentence, then the next one comes;
  // pausing keeps it on the scene. Under reduced motion it doesn't play on its own and
  // nothing slides in. Arrow keys step through scenes, space pauses, Esc ends.
  import { cubicOut } from 'svelte/easing';
  import { fade, fly } from 'svelte/transition';
  import { dalje, idiNa, natrag, reprodukcija, smanjenoKretanje, tekstPrice, zavrsi } from '../stories/player.js';
  import { t } from '../jezik.js';

  const r = $derived($reprodukcija);
  const ukupno = $derived(r?.prica.scene.length ?? 0);
  // In the current language; the card is rebuilt when it changes (App.svelte).
  const naslov = $derived(r ? tekstPrice(r.prica).naslov : '');
  const opis = $derived(r ? tekstPrice(r.prica).opis : '');
  const zadnja = $derived(r ? r.indeks === ukupno - 1 : false);
  const prikaz = $derived(r?.faza === 'prikaz');
  const rijeci = $derived(r?.tekst?.split(/\s+/) ?? []);
  // About 25 characters a second, after the words have come in: 4–8 s a scene.
  const trajanje = $derived(r?.tekst ? Math.min(8000, Math.max(4000, 1200 + r.tekst.length * 38)) : 0);

  const ms = (n) => (smanjenoKretanje ? 0 : n);

  let automatski = $state(!smanjenoKretanje);
  /** @type {HTMLElement | undefined} */
  let okvir = $state();

  // Each story starts playing on its own, with the focus on its controls (the button
  // that started it is hidden with the panels).
  let pricaId = null;
  $effect(() => {
    const id = r?.prica.id ?? null;
    if (id === pricaId) return;
    pricaId = id;
    automatski = !smanjenoKretanje;
    if (id) okvir?.focus({ preventScroll: true });
  });

  // The current step's bar fills over the scene's time; when full, the next scene.
  function scenaIstekla() {
    if (!automatski) return;
    if (zadnja) automatski = false;
    else dalje();
  }

  function onkeydown(e) {
    if (!r || e.defaultPrevented || e.target.closest?.('input, textarea, select')) return;
    if (e.key === 'ArrowRight') dalje();
    else if (e.key === 'ArrowLeft') natrag();
    else if (e.key === 'Escape') zavrsi();
    else if (e.key === ' ' && !e.target.closest?.('button')) automatski = !automatski;
    else return;
    e.preventDefault();
  }
</script>

<svelte:window {onkeydown} />

{#if r}
  <div class="kino">
    <div class="sjena" aria-hidden="true" transition:fade={{ duration: ms(500) }}></div>

    {#if r.faza === 'uvod'}
      <div class="naslovna" aria-hidden="true" in:fly={{ y: 14, duration: ms(700), easing: cubicOut }} out:fade={{ duration: ms(450) }}>
        <p class="nadnaslov">{t('Priča', 'Story')}</p>
        <p class="ime">{naslov}</p>
        <p class="opis">{opis}</p>
      </div>
    {/if}

    <section class="dno" aria-label="{t('Priča', 'Story')}: {naslov}" tabindex="-1" bind:this={okvir}>
      {#if prikaz}
        {#key r.indeks}
          <div class="oblacic" in:fly={{ y: 16, duration: ms(450), easing: cubicOut }} out:fade={{ duration: ms(220) }}>
            <p class="nadnaslov">{naslov}</p>
            <p class="tekst" aria-hidden="true">
              {#each rijeci as rijec, i}<span style="--i: {i}">{rijec}</span>{' '}{/each}
            </p>
          </div>
        {/key}
      {/if}

      <div class="kontrole" transition:fly={{ y: 12, duration: ms(400), easing: cubicOut }}>
        <button type="button" class="ikona" aria-label={t('Prethodna scena', 'Previous scene')} title={t('Prethodna scena (←)', 'Previous scene (←)')} onclick={natrag} disabled={r.faza === 'uvod' || r.indeks === 0}>
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M10 3L5 8l5 5" /></svg>
        </button>
        <button type="button" class="ikona" aria-pressed={automatski} aria-label={t('Automatski', 'Auto-play')} title={automatski ? t('Pauza (razmak)', 'Pause (space)') : t('Pokreni (razmak)', 'Play (space)')} onclick={() => (automatski = !automatski)}>
          {#if automatski}
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M5.5 3.5v9M10.5 3.5v9" /></svg>
          {:else}
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path class="puno" d="M5 3l8 5-8 5z" /></svg>
          {/if}
        </button>

        <div class="koraci" role="group" aria-label={t('Scene', 'Scenes')}>
          {#each r.prica.scene as _, i}
            <button
              type="button"
              class="korak"
              class:gotov={i < r.indeks || (i === r.indeks && prikaz && !automatski)}
              aria-label={t(`Scena ${i + 1} od ${ukupno}`, `Scene ${i + 1} of ${ukupno}`)}
              aria-current={i === r.indeks ? 'step' : undefined}
              disabled={r.faza === 'uvod'}
              onclick={() => idiNa(i)}
            >
              <span class="crta">
                {#if i === r.indeks && prikaz && automatski}
                  {#key r.indeks}
                    <span class="puni" style="animation-duration: {trajanje}ms" onanimationend={scenaIstekla}></span>
                  {/key}
                {/if}
              </span>
            </button>
          {/each}
        </div>

        {#if zadnja && prikaz}
          <button type="button" class="glavni" onclick={zavrsi}>{t('Završi', 'Finish')}</button>
        {:else}
          <button type="button" class="ikona" aria-label={t('Sljedeća scena', 'Next scene')} title={t('Sljedeća scena (→)', 'Next scene (→)')} onclick={dalje} disabled={r.faza === 'uvod'}>
            <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M6 3l5 5-5 5" /></svg>
          </button>
        {/if}
        <button type="button" class="ikona" aria-label={t('Završi priču', 'End story')} title={t('Završi priču (Esc)', 'End story (Esc)')} onclick={zavrsi}>
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" /></svg>
        </button>
      </div>
    </section>

    <!-- What the screen shows, for screen readers: the title, then each sentence. -->
    <p class="sr-only" aria-live="polite">
      {r.faza === 'uvod' ? `${t('Priča', 'Story')}: ${naslov}. ${opis}.`
      : prikaz ? t(`${r.indeks + 1}. od ${ukupno}: ${r.tekst}`, `${r.indeks + 1} of ${ukupno}: ${r.tekst}`)
      : ''}
    </p>
  </div>
{/if}

<style>
  /* Its own dark look on every screen size, like a film's subtitles. */
  .kino {
    --tamno: rgba(20, 22, 27, 0.9);
    --rub: #2c3240;
    --tekst: #eef0f5;
    --blago: #8b93a7;
    --naglasak: #4fd1c5;
    position: absolute;
    inset: 0;
    z-index: 3;
    pointer-events: none;
    font-family: system-ui, sans-serif;
    color: var(--tekst);
  }

  /* Darker edges, like a film frame; the subtitles read on any map below. */
  .sjena {
    position: absolute;
    inset: 0;
    background:
      linear-gradient(to bottom, rgba(8, 10, 16, 0.45), transparent 22%),
      linear-gradient(to top, rgba(8, 10, 16, 0.6), transparent 38%);
  }

  .naslovna {
    position: absolute;
    top: 50%;
    left: 50%;
    width: min(640px, calc(100% - 48px));
    transform: translate(-50%, -50%);
    text-align: center;
    text-shadow: 0 2px 18px rgba(0, 0, 0, 0.55);
  }

  .naslovna .ime {
    margin: 6px 0 10px;
    font-size: clamp(28px, 6vw, 46px);
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.01em;
  }

  .naslovna .opis {
    margin: 0;
    font-size: clamp(15px, 2.4vw, 18px);
    color: #c9cfdb;
  }

  .nadnaslov {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--naglasak);
  }

  .dno {
    position: absolute;
    bottom: calc(34px + env(safe-area-inset-bottom, 0px));
    left: 50%;
    display: grid;
    gap: 10px;
    width: min(600px, calc(100% - 24px));
    transform: translateX(-50%);
    outline: none;
  }

  /* The speech bubble. */
  .oblacic {
    padding: 14px 18px 16px;
    border: 1px solid var(--rub);
    border-radius: 18px;
    background: var(--tamno);
    backdrop-filter: blur(10px);
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.45);
    pointer-events: auto;
  }

  .oblacic .tekst {
    margin: 6px 0 0;
    font-size: clamp(16px, 2.2vw, 19px);
    line-height: 1.5;
  }

  /* The sentence comes in word by word. */
  .tekst span {
    display: inline-block;
    animation: rijec 420ms cubic-bezier(0.2, 0.7, 0.3, 1) both;
    animation-delay: calc(120ms + var(--i) * 45ms);
  }

  @keyframes rijec {
    from {
      opacity: 0;
      transform: translateY(6px);
      filter: blur(3px);
    }
  }

  .kontrole {
    display: flex;
    align-items: center;
    gap: 4px;
    justify-self: center;
    width: 100%;
    box-sizing: border-box;
    padding: 5px;
    border: 1px solid var(--rub);
    border-radius: 999px;
    background: var(--tamno);
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    pointer-events: auto;
  }

  button {
    border: 0;
    background: none;
    color: var(--tekst);
    font: inherit;
    cursor: pointer;
  }

  button:disabled {
    cursor: default;
    opacity: 0.35;
  }

  button:focus-visible {
    outline: 2px solid var(--naglasak);
    outline-offset: 2px;
  }

  .ikona {
    display: grid;
    flex: none;
    place-items: center;
    width: 36px;
    height: 36px;
    padding: 0;
    border-radius: 50%;
  }

  .ikona:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.08);
  }

  .ikona path {
    fill: none;
    stroke: currentColor;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .ikona path.puno {
    fill: currentColor;
    stroke-width: 1;
  }

  .glavni {
    flex: none;
    height: 36px;
    padding: 0 16px;
    border-radius: 999px;
    background: var(--naglasak);
    color: #0b1222;
    font-size: 14px;
    font-weight: 600;
  }

  /* One bar per scene: done ones full, the current one filling while it plays. */
  .koraci {
    display: flex;
    flex: 1;
    gap: 4px;
    min-width: 0;
    padding: 0 6px;
  }

  .korak {
    flex: 1;
    min-width: 0;
    height: 36px;
    padding: 0;
    border-radius: 4px;
  }

  .crta {
    position: relative;
    display: block;
    height: 4px;
    overflow: hidden;
    border-radius: 2px;
    background: rgba(255, 255, 255, 0.18);
    transition: height 150ms ease;
  }

  .korak:hover:not(:disabled) .crta {
    height: 6px;
  }

  .korak.gotov .crta {
    background: var(--naglasak);
  }

  .puni {
    position: absolute;
    inset: 0;
    background: var(--naglasak);
    transform-origin: left;
    animation: puni linear both;
  }

  @keyframes puni {
    from {
      transform: scaleX(0);
    }
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }

  @media (prefers-reduced-motion: reduce) {
    .tekst span {
      animation: none;
    }
  }

  @media (max-width: 640px) {
    .dno {
      bottom: calc(30px + env(safe-area-inset-bottom, 0px));
    }

    .oblacic {
      padding: 12px 14px 14px;
      border-radius: 16px;
    }

    .ikona {
      width: 34px;
      height: 34px;
    }
  }
</style>
