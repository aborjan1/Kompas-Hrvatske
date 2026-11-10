<script>
  // Floating panels over the map. The layer itself lets pointer events through so the
  // map stays draggable between panels; only the panels catch clicks. During a story
  // the whole layer steps aside for the map (html[data-kino], src/raspored.css).
  import GrafoviPanel from './GrafoviPanel.svelte';
  import InfoPanel from './InfoPanel.svelte';
  import IzvorPodatka from './IzvorPodatka.svelte';
  import JezikGumb from './JezikGumb.svelte';
  import Pretraga from './Pretraga.svelte';
  import Putanja from './Putanja.svelte';
  import TemeBar from './TemeBar.svelte';
  import { onMount } from 'svelte';
  import { t } from '../jezik.js';

  // Docked columns on wide screens (src/raspored.css): either column can be closed with
  // its tab. The map frames areas in the free part between the columns, so it is told
  // ('kh:raspored') whenever that part changes, once the columns have finished moving.
  // Read back from the page, so a column stays closed when the panels are rebuilt in
  // another language.
  const html = document.documentElement;
  const zatvoreno = $state({
    lijevo: html.dataset.trakaLijevo === 'zatvorena',
    desno: html.dataset.trakaDesno === 'zatvorena',
  });
  const javiRaspored = () => setTimeout(() => dispatchEvent(new Event('kh:raspored')), 280);

  /** @param {'lijevo' | 'desno'} strana */
  function prebaci(strana) {
    zatvoreno[strana] = !zatvoreno[strana];
    const kljuc = strana === 'lijevo' ? 'trakaLijevo' : 'trakaDesno';
    if (zatvoreno[strana]) html.dataset[kljuc] = 'zatvorena';
    else delete html.dataset[kljuc];
    javiRaspored();
  }

  // The charts column comes and goes with the tema and area (GrafoviPanel), which
  // changes the free part too.
  let grafovi;
  onMount(() => {
    let ima = Boolean(grafovi.querySelector('.kh-panel'));
    const promatrac = new MutationObserver(() => {
      const sada = Boolean(grafovi.querySelector('.kh-panel'));
      if (sada !== ima) javiRaspored();
      ima = sada;
    });
    promatrac.observe(grafovi, { childList: true, subtree: true });
    return () => promatrac.disconnect();
  });
</script>

<div class="sloj">
  <div class="gore">
    <Putanja />
    <div class="vrh">
      <Pretraga />
      <JezikGumb />
    </div>
  </div>
  <div class="lijevo" bind:this={grafovi}><GrafoviPanel /></div>
  <div class="desno"><InfoPanel /></div>
  <div class="dolje">
    <TemeBar />
    <IzvorPodatka />
  </div>
  <!-- Column tabs, shown on wide screens only (raspored.css). -->
  <button
    type="button"
    class="kh-sklopi kh-sklopi-lijevo"
    aria-expanded={!zatvoreno.lijevo}
    aria-label={zatvoreno.lijevo ? t('Otvori podatke', 'Open data') : t('Zatvori podatke', 'Close data')}
    title={zatvoreno.lijevo ? t('Otvori podatke', 'Open data') : t('Zatvori podatke', 'Close data')}
    onclick={() => prebaci('lijevo')}
  >{zatvoreno.lijevo ? '›' : '‹'}</button>
  <button
    type="button"
    class="kh-sklopi kh-sklopi-desno"
    aria-expanded={!zatvoreno.desno}
    aria-label={zatvoreno.desno ? t('Otvori grafove', 'Open charts') : t('Zatvori grafove', 'Close charts')}
    title={zatvoreno.desno ? t('Otvori grafove', 'Open charts') : t('Zatvori grafove', 'Close charts')}
    onclick={() => prebaci('desno')}
  >{zatvoreno.desno ? '‹' : '›'}</button>
</div>

<style>
  .sloj {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    font-size: 14px;
    color: var(--kh-tekst);
    /* Steps aside for a story once its panels have faded, see raspored.css. */
    transition: visibility 300ms;
  }

  .sloj :global(.kh-panel) {
    pointer-events: auto;
  }

  .kh-sklopi {
    display: none;
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

  /* Search with the language switch beside it; the search box gives way on a phone. */
  .vrh {
    display: flex;
    gap: 8px;
    align-items: stretch;
    justify-content: center;
    max-width: 100%;
    min-width: 0;
  }

  .vrh > :global(.pretraga) {
    flex: 1 1 auto;
    min-width: 0;
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
  @media (max-width: 899px) and (orientation: portrait), (max-width: 559px) {
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

    .desno {
      top: auto;
      right: 12px;
      bottom: 180px;
      width: calc(100% - 24px);
      max-height: 40%;
    }
  }
</style>
