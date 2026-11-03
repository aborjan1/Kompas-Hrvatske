<script>
  // One series from nizovi.json over the years for the selected area, as a small line
  // chart with one sentence on the change and the source. Per resident when the map
  // shows per-capita values and the series has a per-capita form. Renders nothing when
  // the area has no data for the series (e.g. unemployment for a municipality).
  import { onDestroy } from 'svelte';
  import {
    CategoryScale,
    Chart,
    Filler,
    LinearScale,
    LineController,
    LineElement,
    PointElement,
    Tooltip,
  } from 'chart.js';
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { nizovi } from '../data/nizovi.js';
  import { formatVrijednost } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  Chart.register(CategoryScale, LinearScale, LineController, LineElement, PointElement, Tooltip, Filler);

  /** @type {{ sid: string }} */
  let { sid } = $props();

  // Shared colours (app.css), so axes read on light and dark panels.
  const bojaTeksta = (ime) => getComputedStyle(document.documentElement).getPropertyValue(ime).trim();
  const smanjenoKretanje =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const postotak = new Intl.NumberFormat('hr-HR', { maximumFractionDigits: 0, signDisplay: 'always' });

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const n = $nizovi.podaci;
    const s = n?.serije[sid];
    if (!s || !podrucje) return null;
    const sirovo = n.podrucja[$view.razina === 'drzava' ? 'HR' : podrucje.sifra]?.[sid];
    if (!sirovo || sirovo.every((v) => v === null)) return null;

    const stanovnika = podrucje.pokazatelji.stanovnistvo;
    const poStanovniku = $view.mjera === 'po-stanovniku' && Boolean(s.po_stanovniku && stanovnika);
    const jedinica = poStanovniku ? s.po_stanovniku.jedinica : s.jedinica;
    const decimale = poStanovniku ? (s.jedinica === 'EUR' ? 0 : 1) : s.decimale;
    const vrijednosti = sirovo.map((v) =>
      v === null ? null : poStanovniku ? (v / stanovnika) * s.po_stanovniku.mnozitelj : v,
    );
    const tekst = (/** @type {number} */ v) => formatVrijednost(v, jedinica, decimale);

    // Change from the first to the last year with data: points for rates, % otherwise.
    const prviI = vrijednosti.findIndex((v) => v !== null);
    const zadnjiI = vrijednosti.findLastIndex((v) => v !== null);
    const prvi = vrijednosti[prviI];
    const zadnji = vrijednosti[zadnjiI];
    let promjena = '';
    if (zadnjiI > prviI) {
      const od = `od ${s.godine[prviI]}.`;
      if (s.jedinica === '%') promjena = `S ${tekst(prvi)} na ${tekst(zadnji)} (${s.godine[prviI]}.–${s.godine[zadnjiI]}.)`;
      else if (prvi) promjena = `${postotak.format((zadnji / prvi - 1) * 100)} % ${od}`;
    }
    const izvor = $podaci.meta?.izvori[s.izvor];
    return {
      naslov: s.naziv + (poStanovniku ? ` – ${s.po_stanovniku.jedinica}` : ''),
      godine: s.godine.map(String),
      vrijednosti,
      tekst,
      kratko: (/** @type {number} */ v) =>
        formatVrijednost(v, jedinica.startsWith('EUR') ? 'EUR' : jedinica === '%' ? '%' : 'broj', 0),
      raspon: `${s.godine[prviI]}.–${s.godine[zadnjiI]}.`,
      zadnji: tekst(zadnji),
      promjena,
      napomena: s.napomena,
      izvor: izvor?.izdavatelj ?? '',
      boja: TEME_POKAZATELJI[$view.tema].boje[3],
      odNule: s.jedinica !== '%' && s.jedinica !== 'osoba',
    };
  });

  /** @type {HTMLCanvasElement | undefined} */
  let canvas = $state();
  /** @type {Chart | undefined} */
  let chart;
  let trenutni = null;

  $effect(() => {
    if (!canvas || !prikaz) return;
    trenutni = prikaz;
    const data = {
      labels: prikaz.godine,
      datasets: [
        {
          label: prikaz.naslov,
          data: prikaz.vrijednosti,
          borderColor: prikaz.boja,
          backgroundColor: `${prikaz.boja}22`,
          fill: true,
          borderWidth: 2.5,
          pointRadius: 2,
          pointHoverRadius: 4,
          tension: 0.25,
          spanGaps: true,
        },
      ],
    };
    if (chart && chart.canvas !== canvas) chart.destroy();
    if (chart && chart.canvas === canvas) {
      chart.data = data;
      chart.options.scales.y.beginAtZero = prikaz.odNule;
      chart.update();
    } else {
      chart = new Chart(canvas, { type: 'line', data, options: opcije(prikaz.odNule) });
    }
  });

  onDestroy(() => chart?.destroy());

  function opcije(odNule) {
    return {
      maintainAspectRatio: false,
      animation: smanjenoKretanje ? false : { duration: 250 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => `${items[0].label}.`,
            label: (item) => ` ${trenutni.tekst(item.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 }, color: bojaTeksta('--kh-tekst-blago'), maxRotation: 0, autoSkipPadding: 6 },
        },
        y: {
          beginAtZero: odNule,
          grid: { color: bojaTeksta('--kh-rub') },
          border: { display: false },
          ticks: {
            font: { size: 10 },
            color: bojaTeksta('--kh-tekst-blago'),
            maxTicksLimit: 4,
            callback: (v) => trenutni.kratko(Number(v)),
          },
        },
      },
    };
  }
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="niz-{sid}">
    <h3 id="niz-{sid}">{prikaz.naslov} <span class="godina">{prikaz.raspon}</span></h3>
    <p class="podnaslov">
      <strong>{prikaz.zadnji}</strong>{#if prikaz.promjena}<span class="promjena">&nbsp;· {prikaz.promjena}</span>{/if}
    </p>
    <div class="platno" aria-hidden="true">
      <canvas bind:this={canvas}></canvas>
    </div>
    <!-- A table ignores a 1px width, so the visually hidden wrapper is a div. -->
    <div class="sr-only">
      <table>
        <caption>{prikaz.naslov}</caption>
        <tbody>
          {#each prikaz.godine as g, i (g)}
            {#if prikaz.vrijednosti[i] !== null}
              <tr><th scope="row">{g}.</th><td>{prikaz.tekst(prikaz.vrijednosti[i])}</td></tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
    <p class="napomena">{prikaz.napomena}{prikaz.izvor ? ` Izvor: ${prikaz.izvor}.` : ''}</p>
  </section>
{/if}

<style>
  .graf {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
  }

  h3 {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    color: var(--kh-tekst);
  }

  .godina {
    font-weight: 400;
    color: var(--kh-tekst-blago);
  }

  .podnaslov {
    margin: 2px 0 4px;
    font-size: 12px;
    color: var(--kh-tekst);
  }

  .promjena {
    color: var(--kh-tekst-blago);
  }

  .platno {
    position: relative;
    height: 110px;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }

  .napomena {
    margin: 4px 0 0;
    font-size: 11px;
    line-height: 1.35;
    color: var(--kh-tekst-blago);
  }
</style>
