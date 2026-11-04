<script>
  // "Preuzmi podatke (CSV)": all indicators of the selected area with their sources, as a
  // file (src/data/csv.js). Built in the browser, nothing is sent anywhere.
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { csvPodrucja } from '../data/csv.js';
  import { t } from '../jezik.js';

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  function preuzmi() {
    if (!podrucje || !$podaci.meta) return;
    const { ime, sadrzaj } = csvPodrucja($podaci, $view.razina, podrucje);
    const url = URL.createObjectURL(new Blob([sadrzaj], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = ime;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
</script>

{#if podrucje && $podaci.meta}
  <p class="preuzmi">
    <button type="button" onclick={preuzmi}>
      <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
        <path d="M8 2v8M4.5 6.8 8 10.3l3.5-3.5M3 13h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      {t('Preuzmi podatke (CSV)', 'Download data (CSV)')}
    </button>
    <span class="opis">
      {t(
        'Svi pokazatelji ovog područja, s izvorom i dozvolom uz svaki broj.',
        'All indicators for this area, with the source and licence of each number.',
      )}
    </span>
  </p>
{/if}

<style>
  .preuzmi {
    margin: 14px 0 2px;
    padding-top: 12px;
    border-top: 1px solid var(--kh-rub);
    font-size: 12px;
    line-height: 1.4;
  }

  button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border: 1px solid var(--kh-rub);
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    color: var(--kh-tekst);
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }

  button:hover {
    border-color: var(--kh-naglasak);
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }

  .opis {
    display: block;
    margin-top: 4px;
    color: var(--kh-tekst-blago);
  }
</style>
