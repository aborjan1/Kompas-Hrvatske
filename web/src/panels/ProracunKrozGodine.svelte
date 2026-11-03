<script>
  // The selected area's local budget over the years (proracuni.json): revenue,
  // expenditure and investment as three lines, per resident when the map shows
  // per-capita values. Novac tema only.
  import { onDestroy } from 'svelte';
  import {
    CategoryScale,
    Chart,
    LinearScale,
    LineController,
    LineElement,
    PointElement,
    Tooltip,
  } from 'chart.js';
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { proracuni, ucitajProracune } from '../data/proracuni.js';
  import { formatVrijednost, postotak } from '../data/format.js';
  import { god, raspon, t } from '../jezik.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  Chart.register(CategoryScale, LinearScale, LineController, LineElement, PointElement, Tooltip);

  $effect(() => ucitajProracune());

  const SIVA = '#8a8983';
  // Shared colours (app.css), so axes read on light and dark panels.
  const bojaTeksta = (ime) => getComputedStyle(document.documentElement).getPropertyValue(ime).trim();
  const smanjenoKretanje =
    typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const p = $proracuni.podaci;
    if (!p || !podrucje) return null;
    const z = p.podrucja[$view.razina === 'drzava' ? 'HR' : podrucje.sifra];
    if (!z) return null;
    const stanovnika = podrucje.pokazatelji.stanovnistvo;
    const poStanovniku = $view.mjera === 'po-stanovniku' && Boolean(stanovnika);
    const djelitelj = poStanovniku ? stanovnika : 1;
    const boja = TEME_POKAZATELJI[$view.tema].boje[3];
    const nizovi = [
      { naziv: t('Prihodi', 'Revenue'), vrijednosti: z.prihodi, boja, crtkano: false },
      { naziv: t('Rashodi', 'Expenditure'), vrijednosti: z.rashodi, boja: SIVA, crtkano: false },
      { naziv: t('Ulaganja', 'Investment'), vrijednosti: z.ulaganja, boja, crtkano: true },
    ].map((n) => ({ ...n, vrijednosti: n.vrijednosti.map((v) => v / djelitelj) }));
    const tekst = (/** @type {number} */ v) =>
      formatVrijednost(v, poStanovniku ? 'EUR po stanovniku' : 'EUR', 0);
    const prvi = p.godine[0];
    const zadnji = p.godine.at(-1);
    const rast = z.prihodi[0] ? (z.prihodi.at(-1) / z.prihodi[0] - 1) * 100 : null;
    return {
      godine: p.godine.map(String),
      nizovi,
      tekst,
      kratko: (/** @type {number} */ v) => formatVrijednost(v, 'EUR', 0),
      poStanovniku,
      prvi,
      zadnji,
      rast,
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
      datasets: prikaz.nizovi.map((n) => ({
        label: n.naziv,
        data: n.vrijednosti,
        borderColor: n.boja,
        backgroundColor: n.boja,
        borderWidth: 2,
        borderDash: n.crtkano ? [5, 4] : [],
        pointRadius: 2,
        pointHoverRadius: 4,
        tension: 0.25,
      })),
    };
    if (chart && chart.canvas !== canvas) chart.destroy();
    if (chart && chart.canvas === canvas) {
      chart.data = data;
      chart.update();
    } else {
      chart = new Chart(canvas, { type: 'line', data, options: opcije() });
    }
  });

  onDestroy(() => chart?.destroy());

  function opcije() {
    return {
      maintainAspectRatio: false,
      animation: smanjenoKretanje ? false : { duration: 250 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => god(items[0].label),
            label: (item) => ` ${item.dataset.label}: ${trenutni.tekst(item.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 }, color: bojaTeksta('--kh-tekst-blago') } },
        y: {
          beginAtZero: true,
          grid: { color: bojaTeksta('--kh-rub') },
          border: { display: false },
          ticks: {
            font: { size: 10 },
            color: bojaTeksta('--kh-tekst-blago'),
            maxTicksLimit: 5,
            callback: (v) => trenutni.kratko(Number(v)),
          },
        },
      },
    };
  }
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="proracun-godine-naslov">
    <h3 id="proracun-godine-naslov">
      {t('Proračun kroz godine', 'Budget over the years')} <span class="godina">{raspon(prikaz.prvi, prikaz.zadnji)}</span>
    </h3>
    {#if prikaz.rast !== null}
      <p class="podnaslov">
        {t(`Prihodi su ${prikaz.rast >= 0 ? 'porasli' : 'pali'}`, `Revenue ${prikaz.rast >= 0 ? 'grew' : 'fell'}`)}
        <strong>{postotak(prikaz.rast, { predznak: true })}</strong>
        {t(`od ${god(prikaz.prvi)}`, `since ${prikaz.prvi}.`)}{prikaz.poStanovniku
          ? t(' Iznosi su po stanovniku.', ' Amounts are per resident.')
          : ''}
      </p>
    {/if}
    <ul class="legenda" aria-hidden="true">
      {#each prikaz.nizovi as n (n.naziv)}
        <li>
          <span class="crta" class:crtkano={n.crtkano} style:border-color={n.boja}></span>{n.naziv}
        </li>
      {/each}
    </ul>
    <div class="platno" aria-hidden="true">
      <canvas bind:this={canvas}></canvas>
    </div>
    <!-- A table ignores a 1px width, so the visually hidden wrapper is a div. -->
    <div class="sr-only">
      <table>
        <caption>{t('Proračun po godinama', 'Budget by year')}{prikaz.poStanovniku ? t(', po stanovniku', ', per resident') : ''}</caption>
        <thead>
          <tr><th scope="col">{t('Godina', 'Year')}</th>{#each prikaz.nizovi as n (n.naziv)}<th scope="col">{n.naziv}</th>{/each}</tr>
        </thead>
        <tbody>
          {#each prikaz.godine as g, i (g)}
            <tr>
              <th scope="row">{god(g)}</th>
              {#each prikaz.nizovi as n (n.naziv)}<td>{prikaz.tekst(n.vrijednosti[i])}</td>{/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="napomena">
      {t(
        'Ulaganja su dio rashoda (ceste, zgrade, oprema). Izvor: Ministarstvo financija.',
        'Investment is part of expenditure (roads, buildings, equipment). Source: Ministry of Finance.',
      )}
    </p>
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
    margin: 2px 0 6px;
    font-size: 12px;
    color: var(--kh-tekst);
  }

  .legenda {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    margin: 0 0 4px;
    padding: 0;
    list-style: none;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  .legenda li {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .crta {
    width: 16px;
    border-top: 2px solid;
  }

  .crta.crtkano {
    border-top-style: dashed;
  }

  .platno {
    position: relative;
    height: 150px;
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
    margin: 6px 0 0;
    font-size: 11px;
    line-height: 1.35;
    color: var(--kh-tekst-blago);
  }
</style>
