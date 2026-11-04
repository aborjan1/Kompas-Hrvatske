<script>
  // "Where the money goes": the selected area's local budget expenditure by function
  // (COFOG) in the last year, largest first, as a share and in euros (per resident when
  // the map shows per-capita values). Novac tema only; data from proracuni.json.
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { proracuni, ucitajProracune, zbrojFunkcija } from '../data/proracuni.js';
  import { formatVrijednost, postotak } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';
  import { god, t } from '../jezik.js';

  $effect(() => ucitajProracune());

  // Everyday names with what most of the money pays for at local level; the official
  // COFOG name is in the tooltip.
  const NAZIVI = {
    '01': t('Uprava i opće usluge', 'Administration and general services'),
    '02': t('Obrana', 'Defence'),
    '03': t('Vatrogasci i sigurnost', 'Fire service and safety'),
    '04': t('Promet, ceste i gospodarstvo', 'Transport, roads and economy'),
    '05': t('Okoliš i otpad', 'Environment and waste'),
    '06': t('Komunalno i uređenje', 'Utilities and public spaces'),
    '07': t('Zdravstvo', 'Health'),
    '08': t('Sport, kultura i religija', 'Sport, culture and religion'),
    '09': t('Vrtići i škole', 'Kindergartens and schools'),
    '10': t('Socijalne pomoći', 'Social support'),
  };
  // Functions under this share go into one "Ostalo" row, so tiny bars don't crowd the list.
  const PRAG_OSTALO = 1.5; // %

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const p = $proracuni.podaci;
    if (!p || !podrucje) return null;
    const z = p.podrucja[$view.razina === 'drzava' ? 'HR' : podrucje.sifra];
    const ukupno = zbrojFunkcija(z);
    if (ukupno <= 0) return null;

    const stanovnika = podrucje.pokazatelji.stanovnistvo;
    const poStanovniku = $view.mjera === 'po-stanovniku' && Boolean(stanovnika);
    // Rows show bare euros; "po stanovniku" is said once, in the line above the list.
    const iznos = (/** @type {number} */ v) =>
      formatVrijednost(poStanovniku ? v / stanovnika : v, 'EUR', 0);

    const sve = Object.entries(z.funkcije)
      .filter(([, v]) => v > 0)
      .map(([f, v]) => ({ f, v, udio: (v / ukupno) * 100 }))
      .sort((a, b) => b.v - a.v);
    const veliki = sve.filter((s) => s.udio >= PRAG_OSTALO);
    const mali = sve.filter((s) => s.udio < PRAG_OSTALO);

    const redovi = veliki.map((s) => ({
      kljuc: s.f,
      naziv: NAZIVI[s.f] ?? p.funkcije[s.f],
      opis: p.funkcije[s.f],
      udio: s.udio,
      iznos: iznos(s.v),
    }));
    if (mali.length) {
      const v = mali.reduce((a, s) => a + s.v, 0);
      redovi.push({
        kljuc: 'ostalo',
        naziv: t('Ostalo', 'Other'),
        opis: mali.map((s) => NAZIVI[s.f] ?? p.funkcije[s.f]).join(', '),
        udio: (v / ukupno) * 100,
        iznos: iznos(v),
      });
    }
    const najveci = Math.max(...redovi.map((r) => r.udio));
    return {
      godina: p.godine.at(-1),
      ukupno: formatVrijednost(
        poStanovniku ? ukupno / stanovnika : ukupno,
        poStanovniku ? 'EUR po stanovniku' : 'EUR',
        0,
      ),
      redovi: redovi.map((r) => ({ ...r, sirina: (r.udio / najveci) * 100 })),
      tko:
        $view.razina !== 'jls' ? t('lokalna samouprava', 'local government')
        : podrucje.vrsta === 'grad' ? t('grad', 'the city')
        : t('općina', 'the municipality'),
      zbirno:
        $view.razina === 'drzava' ? t('Zbroj svih županija, gradova i općina. ', 'Sum of all counties, cities and municipalities. ')
        : $view.razina === 'zupanija' ? t('Zbroj županije i svih njezinih gradova i općina. ', 'Sum of the county and all its cities and municipalities. ')
        : '',
    };
  });

  const boja = $derived(TEME_POKAZATELJI[$view.tema].boje[3]);
  const udio = (/** @type {number} */ u) => (u < 1 ? `<${postotak(1)}` : postotak(u));
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="kamo-ide-novac-naslov">
    <h3 id="kamo-ide-novac-naslov">{t('Kamo ide novac', 'Where the money goes')} <span class="godina">{god(prikaz.godina)}</span></h3>
    <p class="podnaslov">
      {t(`Na što je ${prikaz.tko} potrošila ${prikaz.ukupno}, po namjeni.`, `What ${prikaz.tko} spent ${prikaz.ukupno} on, by purpose.`)}
    </p>
    <ul>
      {#each prikaz.redovi as r (r.kljuc)}
        <li title={r.opis}>
          <span class="naziv">{r.naziv}</span>
          <span class="brojke"><span class="iznos">{r.iznos}</span> <strong>{udio(r.udio)}</strong></span>
          <span class="traka" aria-hidden="true">
            <span style:width="{r.sirina}%" style:background={boja}></span>
          </span>
        </li>
      {/each}
    </ul>
    <p class="napomena">
      {prikaz.zbirno}{t(
        'Ostvarenje, bez prijenosa drugim proračunima. Izvor: Ministarstvo financija.',
        'Outturn, excluding transfers to other budgets. Source: Ministry of Finance.',
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
    margin: 2px 0 8px;
    font-size: 12px;
    color: var(--kh-tekst);
  }

  ul {
    display: grid;
    gap: 6px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    display: grid;
    grid-template-columns: 1fr auto;
    column-gap: 8px;
    row-gap: 2px;
    font-size: 12px;
    line-height: 1.3;
  }

  .naziv {
    color: var(--kh-tekst);
  }

  .brojke {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    color: var(--kh-tekst);
  }

  /* Full row width, so bar lengths compare across rows. */
  .traka {
    grid-column: 1 / -1;
    display: block;
    height: 6px;
    border-radius: 3px;
    background: var(--kh-pozadina-blaga);
    overflow: hidden;
  }

  .traka span {
    display: block;
    height: 100%;
    border-radius: 3px;
  }

  .iznos {
    margin-right: 4px;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  .napomena {
    margin: 8px 0 0;
    font-size: 11px;
    line-height: 1.35;
    color: var(--kh-tekst-blago);
  }
</style>
