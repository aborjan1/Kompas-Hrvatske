<script>
  // Where the selected county stands among all 21 on the indicator the map colours at
  // country level: one bar per county, largest first, the selected one in the tema
  // colour and the rest muted. Clicking a bar selects that county.
  import { onDestroy } from 'svelte';
  import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } from 'chart.js';
  import { selectArea, view } from '../state.js';
  import { ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

  const NEUTRALNA = '#d6d5d1';
  const VISINA_STUPCA = 13; // px per county, bar plus gap

  const usporedba = $derived.by(() => {
    const p = $podaci;
    const v = $view;
    if (!p.meta || !p.zupanije || v.razina !== 'zupanija') return null;
    const kljuc = TEME_POKAZATELJI[v.tema].karta.zupanija;
    const pokazatelj = kljuc ? p.meta.pokazatelji[kljuc] : null;
    if (!pokazatelj?.razine.includes('zupanija')) return null;

    const redovi = [];
    let bezPodatka = 0;
    let poStanovniku = false;
    for (const z of Object.values(p.zupanije)) {
      const o = ocitaj(z, kljuc, pokazatelj, v.mjera);
      poStanovniku = o.poStanovniku;
      if (o.value === null) {
        bezPodatka++;
        continue;
      }
      redovi.push({
        sifra: z.sifra,
        naziv: z.naziv,
        kratko: z.naziv.replace(/ županija$/, ''),
        value: o.value,
        tekst: formatVrijednost(o.value, o.jedinica, o.decimale),
      });
    }
    redovi.sort((a, b) => b.value - a.value);
    const indeks = redovi.findIndex((r) => r.sifra === v.podrucje);

    return {
      naslov: pokazatelj.naziv + (poStanovniku ? ' po stanovniku' : ''),
      godina: pokazatelj.godina,
      redovi,
      indeks,
      ukupno: Object.keys(p.zupanije).length,
      bezPodatka,
      boja: TEME_POKAZATELJI[v.tema].boje[3],
    };
  });

  /** @type {HTMLCanvasElement | undefined} */
  let canvas = $state();
  /** @type {Chart | undefined} */
  let chart;
  // The rows behind the bars, for the click, tooltip and tick callbacks.
  let redovi = [];
  let indeks = -1;

  const smanjenoKretanje =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  $effect(() => {
    const u = usporedba;
    if (!u || !canvas) return;
    redovi = u.redovi;
    indeks = u.indeks;
    const data = {
      labels: u.redovi.map((r) => r.kratko),
      datasets: [
        {
          data: u.redovi.map((r) => r.value),
          backgroundColor: u.redovi.map((_, i) => (i === u.indeks ? u.boja : NEUTRALNA)),
          hoverBackgroundColor: u.redovi.map((_, i) => (i === u.indeks ? u.boja : '#b9b8b2')),
          borderRadius: 4,
          barPercentage: 0.8,
          categoryPercentage: 1,
        },
      ],
    };
    // The canvas is recreated when the chart was hidden (no data) and comes back.
    if (chart && chart.canvas !== canvas) chart.destroy();
    if (chart && chart.canvas === canvas) {
      chart.data = data;
      chart.update();
    } else {
      chart = new Chart(canvas, { type: 'bar', data, options: opcije() });
    }
  });

  onDestroy(() => chart?.destroy());

  function opcije() {
    return {
      indexAxis: 'y',
      maintainAspectRatio: false,
      animation: smanjenoKretanje ? false : { duration: 250 },
      onClick: (_event, elements) => {
        const red = elements.length ? redovi[elements[0].index] : null;
        if (red) selectArea('zupanija', red.sifra);
      },
      onHover: (event, elements) => {
        event.native.target.style.cursor = elements.length ? 'pointer' : '';
      },
      plugins: {
        tooltip: {
          displayColors: false,
          callbacks: {
            title: (items) => redovi[items[0].dataIndex].naziv,
            label: (item) => `${item.dataIndex + 1}. mjesto: ${redovi[item.dataIndex].tekst}`,
          },
        },
      },
      scales: {
        // Values live in the tooltip and the line above the chart, so no value axis.
        x: { display: false, beginAtZero: true },
        y: {
          grid: { display: false },
          border: { display: false },
          ticks: {
            autoSkip: false,
            padding: 4,
            font: (ctx) => ({
              family: 'system-ui, sans-serif',
              size: 11,
              weight: ctx.index === indeks ? 'bold' : 'normal',
            }),
            color: (ctx) => (ctx.index === indeks ? '#1f1f1d' : '#6b6a65'),
          },
        },
      },
    };
  }

  const odabrani = $derived(usporedba && usporedba.indeks >= 0 ? usporedba.redovi[usporedba.indeks] : null);
</script>

{#if usporedba}
  <section class="graf" aria-labelledby="graf-naslov">
    <h3 id="graf-naslov">{usporedba.naslov} <span class="godina">{usporedba.godina}</span></h3>
    {#if odabrani}
      <p class="isticanje">
        <strong>{usporedba.indeks + 1}. od {usporedba.redovi.length}</strong> · {odabrani.tekst}
      </p>
    {:else}
      <p class="isticanje">Za ovu županiju nema podatka.</p>
    {/if}

    <div class="platno" style:height="{usporedba.redovi.length * VISINA_STUPCA + 8}px" aria-hidden="true">
      <canvas bind:this={canvas}></canvas>
    </div>

    {#if usporedba.bezPodatka}
      <p class="napomena">Bez podatka: {usporedba.bezPodatka} od {usporedba.ukupno} županija.</p>
    {/if}

    <table class="sr-only">
      <caption>{usporedba.naslov}, poredak županija</caption>
      <tbody>
        {#each usporedba.redovi as red, i (red.sifra)}
          <tr><th scope="row">{i + 1}. {red.naziv}</th><td>{red.tekst}</td></tr>
        {/each}
      </tbody>
    </table>
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

  .isticanje {
    margin: 2px 0 6px;
    font-size: 13px;
    color: var(--kh-tekst);
  }

  .platno {
    position: relative;
  }

  .napomena {
    margin: 4px 0 0;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
</style>
