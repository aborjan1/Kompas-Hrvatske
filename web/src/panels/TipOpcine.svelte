<script>
  // Type of the selected city or municipality from the machine-learning typology
  // (meta.json `tipologija`, `tip` and `slicni_profil` in jls.json; pipeline/tipologija.py),
  // with the five most similar by their whole profile. Tapping the type explains it;
  // tapping a similar one selects it.
  import { selectArea, view } from '../state.js';
  import { podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';

  const prikaz = $derived.by(() => {
    const p = $podaci;
    const grad = $view.razina === 'jls' ? p.jls?.[$view.podrucje] : null;
    const tipologija = p.meta?.tipologija;
    const tip = grad && tipologija?.tipovi[grad.tip];
    if (!tip) return null;
    const t = tip.tipicno;
    return {
      naziv: tip.naziv,
      opis: tip.opis,
      broj: tip.broj,
      metoda: tipologija.metoda,
      tipicno: [
        `${formatVrijednost(t.stanovnika, 'osoba', 0)} stanovnika`,
        `prosječna dob ${formatVrijednost(t.prosjecna_dob, 'godina', 1)}`,
        `dohodak ${formatVrijednost(t.dohodak_po_stanovniku, 'EUR po stanovniku', 0)}`,
        `${formatVrijednost(t.udio_pomoci, '%', 0)} prihoda iz pomoći`,
      ].join(' · '),
      slicni: (grad.slicni_profil ?? [])
        .map((s) => p.jls[s])
        .filter(Boolean)
        .map((j) => ({ sifra: j.sifra, naziv: j.naziv, zupanija: p.zupanije?.[j.nadredeno]?.naziv ?? '' })),
    };
  });

  let otvoreno = $state(false);
</script>

{#if prikaz}
  <div class="tip">
    <button
      type="button"
      class="naziv"
      aria-expanded={otvoreno}
      aria-controls="tip-objasnjenje"
      title={otvoreno ? 'Sakrij objašnjenje' : 'Što znači ovaj tip?'}
      onclick={() => (otvoreno = !otvoreno)}
    >
      <span class="oznaka">Tip:</span>
      {prikaz.naziv}
      <span class="ikona" aria-hidden="true">i</span>
    </button>
    <div class="objasnjenje" id="tip-objasnjenje" hidden={!otvoreno}>
      <p>{prikaz.opis}</p>
      <p class="sitno">Tipično: {prikaz.tipicno}. Ovom tipu pripada {prikaz.broj} od 556 gradova i općina.</p>
      <p class="sitno"><strong>Kako je izračunato:</strong> {prikaz.metoda}</p>
    </div>
    {#if prikaz.slicni.length}
      <p class="slicni">
        <span class="oznaka">Najsličniji po profilu:</span>
        {#each prikaz.slicni as s, i (s.sifra)}<button
            type="button"
            class="poveznica"
            title={s.zupanija}
            onclick={() => selectArea('jls', s.sifra)}>{s.naziv}</button
          >{i < prikaz.slicni.length - 1 ? ', ' : ''}{/each}
      </p>
    {/if}
  </div>
{/if}

<style>
  .tip {
    margin: -6px 0 12px;
    font-size: 12px;
    line-height: 1.4;
  }

  .naziv {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 0;
    border: 0;
    background: none;
    font: inherit;
    font-weight: 600;
    color: var(--kh-tekst);
    text-align: left;
    cursor: pointer;
  }

  .naziv:focus-visible,
  .poveznica:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
    border-radius: 3px;
  }

  .oznaka {
    font-weight: 400;
    color: var(--kh-tekst-blago);
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
    color: var(--kh-tekst-blago);
  }

  .naziv[aria-expanded='true'] .ikona {
    border-color: var(--kh-naglasak);
    background: var(--kh-naglasak);
    color: #fff;
  }

  .objasnjenje {
    margin-top: 6px;
    padding: 8px 10px;
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    font-size: 12.5px;
    line-height: 1.45;
  }

  .objasnjenje[hidden] {
    display: none;
  }

  .objasnjenje p {
    margin: 0;
  }

  .objasnjenje .sitno {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--kh-tekst-blago);
  }

  .slicni {
    margin: 4px 0 0;
    color: var(--kh-tekst);
  }

  .poveznica {
    padding: 0;
    border: 0;
    background: none;
    font: inherit;
    color: var(--kh-naglasak);
    cursor: pointer;
  }

  .poveznica:hover {
    text-decoration: underline;
  }
</style>
