<script>
  // Info panel: the selected area, up to four numbers for the current tema and one
  // sentence. Proper sentence templates come later (issue "Predlošci rečenica").
  import { view } from '../state.js';
  import { nadjiPodrucje, ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { JEDNOSTAVNI_NAZIVI, TEME_POKAZATELJI } from '../data/teme.js';
  import GrafUsporedbe from './GrafUsporedbe.svelte';
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
          // Official name and note on hover, for anyone who wants the exact definition.
          opis: [pokazatelj.naziv, pokazatelj.napomena].filter(Boolean).join('. '),
          vrijednost: formatVrijednost(o.value, o.jedinica, o.decimale),
          nedostaje: o.value === null,
          godina: pokazatelj.godina,
          napomena: pokazatelj.napomena,
          rang: o.rang,
        };
      });
  });

  const recenica = $derived.by(() => {
    if (!podrucje) return '';
    if ($view.razina === 'drzava') return 'Odaberite županiju na karti za usporedbu.';
    const prvi = brojevi.find((b) => b.rang !== null);
    if (!prvi) return '';
    const od =
      $view.razina === 'zupanija'
        ? `od ${Object.keys($podaci.zupanije ?? {}).length} županija`
        : `od ${Object.keys($podaci.jls ?? {}).length} gradova i općina`;
    return `${prvi.naziv}: ${prvi.rang}. mjesto po veličini ${od}.`;
  });

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

  // Phones only (the button is hidden on wider screens): the panel drops down to its
  // title so the map is visible, and the arrow brings it back. Kept while browsing,
  // so tapping around the map doesn't keep covering it.
  let sklopljeno = $state(false);
</script>

<aside class="kh-panel info" class:sklopljeno aria-live="polite">
  {#if $podaci.greska}
    <p class="poruka">{$podaci.greska}</p>
  {:else if !podrucje}
    <p class="poruka">Učitavanje…</p>
  {:else}
    <div class="zaglavlje">
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
        onclick={() => (sklopljeno = !sklopljeno)}
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
              <dt title={b.opis}>{b.naziv}</dt>
              <dd class:nedostaje={b.nedostaje}>{b.vrijednost}</dd>
              <dd class="godina">{b.godina}</dd>
            </div>
          {/each}
        </dl>
      {:else}
        <p class="poruka">Za ovu temu nema podataka na ovoj razini.</p>
      {/if}

      {#if recenica}<p class="recenica">{recenica}</p>{/if}

      {#if $view.razina === 'zupanija'}<GrafUsporedbe />{/if}
      {#if $view.razina === 'jls'}<UsporedbaSlicnih />{/if}
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

  dd:not(.godina) {
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

    .sklopljeno .detalji {
      display: none;
    }
  }

  @media (max-width: 640px) and (prefers-reduced-motion: reduce) {
    .ladica svg {
      transition: none;
    }
  }
</style>
