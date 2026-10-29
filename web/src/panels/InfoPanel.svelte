<script>
  // Info panel: the selected area, up to four numbers for the current tema and one
  // sentence. Proper sentence templates come later (issue "Predlošci rečenica").
  import { view } from '../state.js';
  import { nadjiPodrucje, ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { JEDNOSTAVNI_NAZIVI, TEME_POKAZATELJI } from '../data/teme.js';
  import GrafUsporedbe from './GrafUsporedbe.svelte';

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
        : 'među gradovima i općinama';
    return `${prvi.naziv}: ${prvi.rang}. mjesto po veličini ${od}.`;
  });

  const temaNaziv = $derived($podaci.meta?.teme[$view.tema] ?? $view.tema);
</script>

<aside class="kh-panel info" aria-live="polite">
  {#if $podaci.greska}
    <p class="poruka">{$podaci.greska}</p>
  {:else if !podrucje}
    <p class="poruka">Učitavanje…</p>
  {:else}
    <p class="tema" style:color={TEME_POKAZATELJI[$view.tema].boje[3]}>{temaNaziv}</p>
    <h2>{podrucje.naziv}</h2>

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
  {/if}
</aside>

<style>
  .info {
    padding: 14px 16px;
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
    margin: 2px 0 12px;
    font-size: 18px;
    line-height: 1.25;
    color: var(--kh-tekst);
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
</style>
