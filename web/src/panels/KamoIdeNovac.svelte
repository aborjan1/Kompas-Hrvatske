<script>
  // "Where the money goes": the selected area's local budget expenditure by function
  // (COFOG) in the last year, largest first, as a share and in euros (per resident when
  // the map shows per-capita values). Novac tema only; data from proracuni.json.
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { proracuni, ucitajProracune } from '../data/proracuni.js';
  import { formatVrijednost } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  $effect(() => ucitajProracune());

  // Everyday names with what most of the money pays for at local level; the official
  // COFOG name is in the tooltip.
  const NAZIVI = {
    '01': 'Uprava i opće usluge',
    '02': 'Obrana',
    '03': 'Vatrogasci i sigurnost',
    '04': 'Promet, ceste i gospodarstvo',
    '05': 'Okoliš i otpad',
    '06': 'Komunalno i uređenje',
    '07': 'Zdravstvo',
    '08': 'Sport, kultura i religija',
    '09': 'Vrtići i škole',
    '10': 'Socijalne pomoći',
  };
  // Functions under this share go into one "Ostalo" row, so tiny bars don't crowd the list.
  const PRAG_OSTALO = 1.5; // %

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const p = $proracuni.podaci;
    if (!p || !podrucje) return null;
    const z = p.podrucja[$view.razina === 'drzava' ? 'HR' : podrucje.sifra];
    if (!z) return null;
    const ukupno = Object.values(z.funkcije).reduce((a, b) => a + b, 0);
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
        naziv: 'Ostalo',
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
        $view.razina !== 'jls' ? 'lokalna samouprava' : podrucje.vrsta === 'grad' ? 'grad' : 'općina',
      zbirno:
        $view.razina === 'drzava' ? 'Zbroj svih županija, gradova i općina. '
        : $view.razina === 'zupanija' ? 'Zbroj županije i svih njezinih gradova i općina. '
        : '',
    };
  });

  const boja = $derived(TEME_POKAZATELJI[$view.tema].boje[3]);
  const cijeli = new Intl.NumberFormat('hr-HR', { maximumFractionDigits: 0 });
  const udio = (/** @type {number} */ u) => (u < 1 ? '<1' : cijeli.format(u));
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="kamo-ide-novac-naslov">
    <h3 id="kamo-ide-novac-naslov">Kamo ide novac <span class="godina">{prikaz.godina}.</span></h3>
    <p class="podnaslov">
      Na što je {prikaz.tko} potrošila
      {prikaz.ukupno}, po namjeni.
    </p>
    <ul>
      {#each prikaz.redovi as r (r.kljuc)}
        <li title={r.opis}>
          <span class="naziv">{r.naziv}</span>
          <span class="brojke"><span class="iznos">{r.iznos}</span> <strong>{udio(r.udio)} %</strong></span>
          <span class="traka" aria-hidden="true">
            <span style:width="{r.sirina}%" style:background={boja}></span>
          </span>
        </li>
      {/each}
    </ul>
    <p class="napomena">
      {prikaz.zbirno}Ostvarenje, bez
      prijenosa drugim proračunima. Izvor: Ministarstvo financija.
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
