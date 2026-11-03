<script>
  // Graph of links in public procurement for the selected area (nabava.json): the area in
  // the middle, its biggest suppliers around it, and on the outer ring other cities and
  // municipalities that have contracts with the same suppliers. The picture is visual
  // only; the list under it carries the same information and the clickable links.
  import { selectArea, view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { nabava, ucitajNabavu } from '../data/nabava.js';
  import { formatVrijednost } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';

  $effect(() => ucitajNabavu());

  const U_GRAFU = 6; // suppliers drawn
  const VEZA_PO_DOBAVLJACU = 3; // other cities and municipalities drawn per supplier
  const SREDINA = 150;

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const n = $nabava.podaci;
    if (!n || !podrucje) return null;
    const sifra = $view.razina === 'drzava' ? 'HR' : podrucje.sifra;
    const z = n.podrucja[sifra];
    if (!z) return null;
    const naziv = (s) => $podaci.jls?.[s]?.naziv ?? s;
    const dobavljaci = z.dobavljaci.map((d) => ({
      ...d,
      tekst: formatVrijednost(d.iznos, 'EUR', 0),
      drugiNazivi: d.drugi.map((s) => ({ sifra: s, naziv: naziv(s) })),
    }));

    // Layout: suppliers on an inner ring, their other clients on an outer ring next to them.
    const uGrafu = dobavljaci.slice(0, U_GRAFU);
    const najveciUdio = Math.max(1, ...uGrafu.map((d) => d.udio ?? 0));
    const cvorovi = uGrafu.map((d, i) => {
      const kut = (i / uGrafu.length) * 2 * Math.PI - Math.PI / 2;
      return {
        ...d,
        x: SREDINA + 78 * Math.cos(kut),
        y: SREDINA + 78 * Math.sin(kut),
        r: 6 + 12 * Math.sqrt((d.udio ?? 0) / najveciUdio),
        kut,
        kratko: d.naziv.length > 20 ? `${d.naziv.slice(0, 19)}…` : d.naziv,
      };
    });
    /** @type {Map<string, { x: number, y: number, naziv: string }>} */
    const vanjski = new Map();
    const linije = [];
    cvorovi.forEach((c, i) => {
      c.drugi.slice(0, VEZA_PO_DOBAVLJACU).forEach((s, j) => {
        if (!vanjski.has(s)) {
          const kut = c.kut + (j - 1) * 0.22 + (i % 2 ? 0.05 : -0.05);
          vanjski.set(s, { x: SREDINA + 132 * Math.cos(kut), y: SREDINA + 132 * Math.sin(kut), naziv: naziv(s) });
        }
        const o = vanjski.get(s);
        linije.push({ x1: c.x, y1: c.y, x2: o.x, y2: o.y });
      });
    });

    return {
      razdoblje: n.razdoblje,
      ugovora: z.ugovora,
      dobavljaci,
      cvorovi,
      vanjski: [...vanjski.values()],
      linije,
      boja: TEME_POKAZATELJI[$view.tema].boje[3],
      svijetla: TEME_POKAZATELJI[$view.tema].boje[1],
      naziv: podrucje.naziv,
      jls: $view.razina === 'jls',
    };
  });
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="graf-veza-naslov">
    <h3 id="graf-veza-naslov">Graf veza: dobavljači <span class="godina">{prikaz.razdoblje}</span></h3>
    {#if !prikaz.dobavljaci.length}
      <p class="napomena">
        U registru javne nabave nema ugovora u ovom razdoblju. Manje nabave (jednostavna nabava)
        ne moraju se ondje objavljivati.
      </p>
    {:else}
      <p class="podnaslov">
        Najveći dobavljači i {prikaz.jls ? 'drugi gradovi i općine' : 'gradovi i općine'} s kojima
        isti dobavljači imaju ugovore.
      </p>
      <svg viewBox="0 0 300 300" class="mreza" aria-hidden="true">
        {#each prikaz.linije as l, i (i)}
          <line x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} class="veza-van" />
        {/each}
        {#each prikaz.cvorovi as c (c.naziv)}
          <line x1={SREDINA} y1={SREDINA} x2={c.x} y2={c.y} class="veza" style:stroke={prikaz.boja} />
        {/each}
        {#each prikaz.vanjski as o (o.naziv)}
          <circle cx={o.x} cy={o.y} r="3.5" class="vanjski"><title>{o.naziv}</title></circle>
        {/each}
        {#each prikaz.cvorovi as c (c.naziv)}
          <circle cx={c.x} cy={c.y} r={c.r} fill={prikaz.svijetla} stroke={prikaz.boja} stroke-width="1.5">
            <title>{c.naziv}: {c.tekst}</title>
          </circle>
          <text
            x={c.x}
            y={c.y + (Math.sin(c.kut) >= 0 ? c.r + 10 : -c.r - 4)}
            text-anchor="middle"
            class="oznaka">{c.kratko}</text
          >
        {/each}
        <circle cx={SREDINA} cy={SREDINA} r="20" fill={prikaz.boja} />
        <text x={SREDINA} y={SREDINA + 3.5} text-anchor="middle" class="sredina"
          >{prikaz.naziv.length > 9 ? `${prikaz.naziv.slice(0, 8)}…` : prikaz.naziv}</text
        >
      </svg>

      <ol class="popis">
        {#each prikaz.dobavljaci as d (d.naziv)}
          <li>
            <div class="red">
              <span class="ime">{d.naziv}</span>
              <span class="iznos">{d.tekst}{d.udio !== null ? ` · ${Math.round(d.udio)} %` : ''}</span>
            </div>
            {#if d.drugih_jls}
              <p class="drugi">
                Ugovore ima i s još {d.drugih_jls}
                {d.drugih_jls % 10 === 1 && d.drugih_jls % 100 !== 11 ? 'gradom ili općinom' : 'gradova i općina'}{d.drugiNazivi.length
                  ? ': '
                  : ''}{#each d.drugiNazivi.slice(0, 3) as g, i (g.sifra)}<button
                    type="button"
                    class="poveznica"
                    onclick={() => selectArea('jls', g.sifra)}>{g.naziv}</button
                  >{i < Math.min(3, d.drugiNazivi.length) - 1 ? ', ' : ''}{/each}{d.drugih_jls > 3 ? ' …' : ''}
              </p>
            {/if}
          </li>
        {/each}
      </ol>
      <p class="napomena">
        {prikaz.ugovora} ugovora uprave {prikaz.jls ? 'grada ili općine' : 'županije, gradova i općina'}.
        Isti dobavljač kod više naručitelja je uobičajen (npr. opskrba strujom) i sam po sebi nije
        nepravilnost. Izvor: registar ugovora EOJN RH.
      </p>
    {/if}
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

  .mreza {
    display: block;
    width: 100%;
    max-width: 300px;
    margin: 0 auto;
  }

  .veza {
    stroke-width: 1.5;
    opacity: 0.7;
  }

  .veza-van {
    stroke: var(--kh-tekst-blago);
    stroke-width: 0.8;
    opacity: 0.45;
  }

  .vanjski {
    fill: var(--kh-tekst-blago);
  }

  .oznaka {
    font-size: 9px;
    fill: var(--kh-tekst);
  }

  .sredina {
    font-size: 9px;
    font-weight: 700;
    fill: #fff;
  }

  .popis {
    display: grid;
    gap: 6px;
    margin: 6px 0 0;
    padding-left: 18px;
    font-size: 12px;
  }

  .red {
    display: flex;
    justify-content: space-between;
    gap: 8px;
  }

  .ime {
    color: var(--kh-tekst);
  }

  .iznos {
    flex: none;
    font-variant-numeric: tabular-nums;
    color: var(--kh-tekst-blago);
  }

  .drugi {
    margin: 1px 0 0;
    font-size: 11px;
    color: var(--kh-tekst-blago);
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

  .poveznica:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
    border-radius: 3px;
  }

  .napomena {
    margin: 6px 0 0;
    font-size: 11px;
    line-height: 1.35;
    color: var(--kh-tekst-blago);
  }
</style>
