<script>
  // Horizontal bar chart for the panels: one bar per row in the given order, the
  // selected row in the tema colour and the rest muted, values in the tooltip only.
  // Clicking a bar calls `onodaberi` with its row. Shared by the county comparison and
  // the comparison with similar cities and municipalities.
  import { onDestroy } from 'svelte';
  import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } from 'chart.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip);

  /**
   * @typedef {object} Redak
   * @property {string} id
   * @property {string} oznaka Label next to the bar.
   * @property {string} naziv Full name, the tooltip title.
   * @property {number} value
   * @property {string[]} detalji Tooltip lines.
   */

  /** @type {{ redovi: Redak[], odabrani: string | null, boja: string, naslov: string,
   *   visinaRetka?: number, onodaberi: (red: Redak) => void }} */
  let { redovi, odabrani, boja, naslov, visinaRetka = 13, onodaberi } = $props();

  const NEUTRALNA = '#d6d5d1';
  const NEUTRALNA_HOVER = '#b9b8b2';

  /** @type {HTMLCanvasElement | undefined} */
  let canvas = $state();
  /** @type {Chart | undefined} */
  let chart;
  // Current rows and selection, for the click, tooltip and tick callbacks.
  let trenutni = [];
  let indeks = -1;

  const smanjenoKretanje =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  $effect(() => {
    if (!canvas) return;
    trenutni = redovi;
    indeks = redovi.findIndex((r) => r.id === odabrani);
    const data = {
      labels: redovi.map((r) => r.oznaka),
      datasets: [
        {
          data: redovi.map((r) => r.value),
          backgroundColor: redovi.map((_, i) => (i === indeks ? boja : NEUTRALNA)),
          hoverBackgroundColor: redovi.map((_, i) => (i === indeks ? boja : NEUTRALNA_HOVER)),
          borderRadius: 4,
          barPercentage: 0.8,
          categoryPercentage: 1,
        },
      ],
    };
    // The canvas is recreated when the parent hid the chart and shows it again.
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
        const red = elements.length ? trenutni[elements[0].index] : null;
        if (red) onodaberi(red);
      },
      onHover: (event, elements) => {
        event.native.target.style.cursor = elements.length ? 'pointer' : '';
      },
      plugins: {
        tooltip: {
          displayColors: false,
          callbacks: {
            title: (items) => trenutni[items[0].dataIndex].naziv,
            label: (item) => trenutni[item.dataIndex].detalji,
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
</script>

<div class="platno" style:height="{redovi.length * visinaRetka + 8}px" aria-hidden="true">
  <canvas bind:this={canvas}></canvas>
</div>

<table class="sr-only">
  <caption>{naslov}</caption>
  <tbody>
    {#each redovi as red (red.id)}
      <tr><th scope="row">{red.naziv}</th><td>{red.detalji.join(', ')}</td></tr>
    {/each}
  </tbody>
</table>

<style>
  .platno {
    position: relative;
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
