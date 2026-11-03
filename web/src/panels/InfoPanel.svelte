<script>
  // Info panel: the selected area, up to four numbers for the current tema and one
  // sentence about them (templates in src/data/recenice.js).
  import { view } from '../state.js';
  import { nadjiPodrucje, ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { napraviRecenicu } from '../data/recenice.js';
  import { JEDNOSTAVNI_NAZIVI, TEME_POKAZATELJI } from '../data/teme.js';
  import EuProjektiPopis from './EuProjektiPopis.svelte';
  import GradskiFiltri from './GradskiFiltri.svelte';
  import GrafUsporedbe from './GrafUsporedbe.svelte';
  import KamoIdeNovac from './KamoIdeNovac.svelte';
  import ProracunKrozGodine from './ProracunKrozGodine.svelte';
  import { siroko } from './ekran.js';
  import PopisPrica from './PopisPrica.svelte';
  import UsporedbaSlicnih from './UsporedbaSlicnih.svelte';

  const MAX_BROJEVA = 4;

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const brojevi = $derived.by(() => {
    const meta = $podaci.meta;
    if (!meta || !podrucje) return [];
    return TEME_POKAZATELJI[$view.tema].panel[$view.razina]
      .filter((kljuc) => meta.pokazatelji[kljuc]?.razine.includes($view.razina))
      .slice(0, MAX_BROJEVA)
      .map((kljuc) => {
        const pokazatelj = meta.pokazatelji[kljuc];
        const o = ocitaj(podrucje, kljuc, pokazatelj, $view.mjera);
        return {
          kljuc,
          naziv: JEDNOSTAVNI_NAZIVI[kljuc] ?? pokazatelj.naziv,
          vrijednost: formatVrijednost(o.value, o.jedinica, o.decimale),
          nedostaje: o.value === null,
          godina: pokazatelj.godina,
          // Shown when the name is tapped: what the number means in plain words, then
          // the official name and how it is calculated, for the exact definition.
          objasnjenje: pokazatelj.objasnjenje,
          sluzbeniNaziv: pokazatelj.naziv,
          napomena: pokazatelj.napomena,
          poStanovniku: o.poStanovniku,
        };
      });
  });

  const recenica = $derived(napraviRecenicu($podaci, $view));

  // City or municipality profile: what it is, where, and how big.
  const podnaslov = $derived.by(() => {
    if ($view.razina !== 'jls' || !podrucje) return '';
    const stanovnika = podrucje.pokazatelji.stanovnistvo;
    return [
      podrucje.vrsta === 'grad' ? 'Grad' : 'Općina',
      $podaci.zupanije?.[podrucje.nadredeno]?.naziv,
      stanovnika != null && `${formatVrijednost(stanovnika, 'osoba', 0)} stanovnika`,
    ]
      .filter(Boolean)
      .join(' · ');
  });

  const temaNaziv = $derived($podaci.meta?.teme[$view.tema] ?? $view.tema);

  // Which number's explanation is open. One at a time, so the panel stays short.
  /** @type {string | null} */
  let otvoreno = $state(null);

  // Phones only (the button is hidden on wider screens): the panel is a bottom sheet
  // with three heights, like phone map apps: `mala` (name and the first number, the map
  // free), `pola` (half the screen) and `puna` (almost all, with the charts). Kept while
  // browsing, so tapping around the map doesn't keep covering it.
  const VISINE = /** @type {const} */ (['mala', 'pola', 'puna']);
  let visina = $state(/** @type {(typeof VISINE)[number]} */ ('mala'));
  const sklopljeno = $derived(visina === 'mala');
  const korak = (smjer) => {
    visina = VISINE[Math.min(Math.max(VISINE.indexOf(visina) + smjer, 0), VISINE.length - 1)];
  };

  // A swipe on the title row moves the sheet a step up or down, next to the arrow.
  // Touch and pen only: a mouse has the arrow.
  const PRAG_POVLACENJA = 30; // px
  let pocetakY = null;

  function onpointerdown(e) {
    if (e.pointerType !== 'mouse') pocetakY = e.clientY;
  }

  function onpointerup(e) {
    if (pocetakY === null) return;
    const pomak = e.clientY - pocetakY;
    pocetakY = null;
    if (pomak > PRAG_POVLACENJA) korak(-1);
    else if (pomak < -PRAG_POVLACENJA) korak(1);
  }
</script>

<aside class="kh-panel info" class:sklopljeno class:puna={visina === 'puna'} aria-live="polite">
  {#if $podaci.greska}
    <p class="poruka">{$podaci.greska}</p>
  {:else if !podrucje}
    <p class="poruka">Učitavanje…</p>
  {:else}
    <!-- The swipe only adds to the arrow button, which keyboards and screen readers use. -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="zaglavlje" {onpointerdown} {onpointerup} onpointercancel={() => (pocetakY = null)}>
      <div class="naslov">
        <p class="tema" style:color={TEME_POKAZATELJI[$view.tema].boje[3]}>{temaNaziv}</p>
        <h2>{podrucje.naziv}</h2>
      </div>
      <button
        type="button"
        class="ladica"
        aria-expanded={!sklopljeno}
        aria-controls="info-detalji"
        aria-label={sklopljeno ? 'Prikaži podatke' : 'Sakrij podatke'}
        title={sklopljeno ? 'Prikaži podatke' : 'Sakrij podatke'}
        onclick={() => (visina = sklopljeno ? 'pola' : 'mala')}
      >
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
          <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>

    <div id="info-detalji" class="detalji">
      {#if podnaslov}<p class="podnaslov">{podnaslov}</p>{/if}

      {#if brojevi.length}
        <dl>
          {#each brojevi as b (b.kljuc)}
            <div class="broj">
              <dt>
                <button
                  type="button"
                  class="pitanje"
                  aria-expanded={otvoreno === b.kljuc}
                  aria-controls="objasnjenje-{b.kljuc}"
                  title={otvoreno === b.kljuc ? 'Sakrij objašnjenje' : 'Što znači ovaj broj?'}
                  onclick={() => (otvoreno = otvoreno === b.kljuc ? null : b.kljuc)}
                >
                  {b.naziv}
                  <span class="ikona" aria-hidden="true">i</span>
                </button>
              </dt>
              <dd class:nedostaje={b.nedostaje}>{b.vrijednost}</dd>
              <dd class="godina">{b.godina}</dd>
              <dd class="objasnjenje" id="objasnjenje-{b.kljuc}" hidden={otvoreno !== b.kljuc}>
                {#if b.objasnjenje}<p>{b.objasnjenje}</p>{/if}
                {#if b.poStanovniku}
                  <p class="kako">Po stanovniku: ukupni iznos podijeljen brojem stanovnika iz Popisa 2021.</p>
                {/if}
                {#if b.napomena}
                  <p class="kako"><strong>Kako je izračunato:</strong> {b.napomena}</p>
                {/if}
                <p class="kako"><strong>Službeni naziv:</strong> {b.sluzbeniNaziv}</p>
              </dd>
            </div>
          {/each}
        </dl>
      {:else}
        <p class="poruka">Za ovu temu nema podataka na ovoj razini.</p>
      {/if}

      {#if recenica}<p class="recenica">{recenica}</p>{/if}

      <!-- Wide screens show these in the chart panel in the top-left corner (GrafoviPanel). -->
      {#if $view.tema === 'novac' && $view.razina !== 'drzava' && !$siroko}
        <KamoIdeNovac />
        <ProracunKrozGodine />
      {/if}

      {#if $view.razina === 'drzava'}<PopisPrica />{/if}
      {#if $view.razina === 'zupanija'}<GrafUsporedbe />{/if}
      {#if $view.razina === 'jls'}<GradskiFiltri /><EuProjektiPopis /><UsporedbaSlicnih />{/if}
    </div>
  {/if}
</aside>

<style>
  .info {
    padding: 14px 16px;
  }

  .zaglavlje {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .naslov {
    flex: 1;
    min-width: 0;
  }

  .ladica {
    display: none;
  }

  .tema {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--kh-naglasak);
  }

  h2 {
    margin: 2px 0 4px;
    font-size: 18px;
    line-height: 1.25;
    color: var(--kh-tekst);
  }

  /* Spacing between the title and the details lives here, not in a negative margin:
     on phones the title row is sticky and would cover anything pulled up under it. */
  .detalji {
    padding-top: 8px;
  }

  .podnaslov {
    margin: -4px 0 12px;
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }

  dl {
    display: grid;
    gap: 10px;
    margin: 0;
  }

  .broj {
    display: grid;
    grid-template-columns: 1fr auto;
    column-gap: 8px;
  }

  dt {
    grid-column: 1 / -1;
    font-size: 13px;
    color: var(--kh-tekst-blago);
  }

  dd {
    margin: 0;
  }

  .pitanje {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 0;
    border: 0;
    background: none;
    font: inherit;
    color: inherit;
    text-align: left;
    cursor: pointer;
  }

  .pitanje:hover,
  .pitanje[aria-expanded='true'] {
    color: var(--kh-tekst);
  }

  .pitanje:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
    border-radius: 3px;
  }

  .ikona {
    display: inline-grid;
    flex: none;
    place-items: center;
    width: 15px;
    height: 15px;
    border: 1px solid currentColor;
    border-radius: 50%;
    font-family: Georgia, serif;
    font-size: 10px;
    font-style: italic;
    font-weight: 700;
    line-height: 1;
  }

  .pitanje[aria-expanded='true'] .ikona {
    border-color: var(--kh-naglasak);
    background: var(--kh-naglasak);
    color: #fff;
  }

  .objasnjenje {
    grid-column: 1 / -1;
    margin-top: 6px;
    padding: 8px 10px;
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    font-size: 12.5px;
    line-height: 1.45;
    color: var(--kh-tekst);
  }

  .objasnjenje[hidden] {
    display: none;
  }

  .objasnjenje p {
    margin: 0;
  }

  .objasnjenje .kako {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--kh-tekst-blago);
  }

  dd:not(.godina):not(.objasnjenje) {
    font-size: 20px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--kh-tekst);
  }

  dd.nedostaje {
    font-size: 14px;
    font-weight: 400;
    font-style: italic;
    color: var(--kh-tekst-blago);
  }

  .godina {
    align-self: end;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  .recenica {
    margin: 12px 0 0;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
    font-size: 13px;
    line-height: 1.4;
  }

  .poruka {
    margin: 0;
    font-size: 13px;
    color: var(--kh-tekst-blago);
  }

  /* Phones: an arrow drops the panel down to its title and brings it back. The title
     row stays at the top while the details scroll under it. */
  @media (max-width: 640px) {
    .zaglavlje {
      position: sticky;
      top: 0;
      z-index: 1;
      margin: -14px -16px 0;
      padding: 14px 16px 4px;
      border-radius: 8px 8px 0 0;
      background: #fff;
      /* The swipe is ours, not a scroll of the panel. */
      touch-action: none;
    }

    .ladica {
      display: grid;
      flex: none;
      place-items: center;
      width: 32px;
      height: 32px;
      margin: -2px -6px 0 0;
      padding: 0;
      border: 0;
      border-radius: 50%;
      background: var(--kh-pozadina-blaga);
      color: var(--kh-tekst);
      cursor: pointer;
    }

    .ladica:focus-visible {
      outline: 2px solid var(--kh-naglasak);
      outline-offset: 2px;
    }

    .ladica svg {
      transition: transform 200ms ease;
    }

    .sklopljeno .ladica svg {
      transform: rotate(180deg);
    }

    .sklopljeno {
      padding-block: 10px;
    }

    .sklopljeno .zaglavlje {
      margin-top: -10px;
      padding-top: 10px;
      padding-bottom: 0;
      border-radius: 8px;
    }

    .sklopljeno h2 {
      margin-bottom: 0;
      font-size: 16px;
    }

    /* The lowest height still shows the first number under the name. */
    /* :global, because charts and lists are other components with their own scope. */
    .sklopljeno .detalji > :global(:not(dl)),
    .sklopljeno dl > :not(:first-child),
    .sklopljeno dd.godina {
      display: none;
    }

    .sklopljeno dl {
      margin-top: 6px;
    }
  }

  @media (max-width: 640px) and (prefers-reduced-motion: reduce) {
    .ladica svg {
      transition: none;
    }
  }
</style>
