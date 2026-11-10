<script>
  // „Što je neobično ovdje”: up to three indicators where the selected city or
  // municipality differs most from others of the same type (uvidi.json,
  // pipeline/uvidi.py). A row opens its tema, per resident where the number is.
  import { setMjera, setTema, view } from '../state.js';
  import { podaci } from '../data/podaci.js';
  import { uvidi, ucitajUvide } from '../data/uvidi.js';
  import { broj, formatVrijednost, postotak } from '../data/format.js';
  import { TEME_POKAZATELJI, jednostavniNaziv } from '../data/teme.js';
  import { t } from '../jezik.js';

  $effect(() => ucitajUvide());

  /**
   * "4,1 puta više nego kod sličnih", "35 % manje …" (amounts); "3,1 p. b. više …",
   * "2,4 god. više …" (shares, age). English: "4.1 times as much as similar places", …
   */
  function usporedba(u, pokazatelj) {
    const vise = u.smjer === 'vise';
    if (pokazatelj.jedinica === '%' || pokazatelj.jedinica === 'godina') {
      const d = broj(1).format(Math.abs(u.vrijednost - u.slicni));
      const pb = pokazatelj.jedinica === '%';
      return t(
        `${d} ${pb ? 'p. b.' : 'god.'} ${vise ? 'više' : 'manje'} nego kod sličnih`,
        `${d} ${pb ? 'pp' : 'yrs'} ${vise ? 'higher' : 'lower'} than similar places`,
      );
    }
    const r = u.vrijednost / u.slicni;
    if (r >= 1.5) {
      return t(`${broj(1).format(r)} puta više nego kod sličnih`, `${broj(1).format(r)} times as much as similar places`);
    }
    const p = postotak(Math.abs(r - 1) * 100);
    return vise
      ? t(`${p} više nego kod sličnih`, `${p} more than similar places`)
      : t(`${p} manje nego kod sličnih`, `${p} less than similar places`);
  }

  const prikaz = $derived.by(() => {
    const p = $podaci;
    const d = $uvidi.podaci;
    const grad = $view.razina === 'jls' ? p.jls?.[$view.podrucje] : null;
    if (!d || !p.meta || !grad?.tip) return null;
    const tip = p.meta.tipologija?.tipovi[grad.tip];
    const redovi = (d.podrucja[grad.sifra] ?? [])
      .filter((u) => p.meta.pokazatelji[u.kljuc])
      .map((u) => {
        const pokazatelj = p.meta.pokazatelji[u.kljuc];
        const jedinica = u.po_stanovniku ? pokazatelj.po_stanovniku.jedinica : pokazatelj.jedinica;
        const decimale = u.po_stanovniku ? (pokazatelj.jedinica === 'EUR' ? 0 : 1) : pokazatelj.decimale;
        return {
          kljuc: u.kljuc,
          tema: pokazatelj.tema,
          temaNaziv: p.meta.teme[pokazatelj.tema] ?? pokazatelj.tema,
          boja: TEME_POKAZATELJI[pokazatelj.tema]?.boje[3],
          poStanovniku: u.po_stanovniku,
          naziv: jednostavniNaziv(u.kljuc, pokazatelj),
          vrijednost: formatVrijednost(u.vrijednost, jedinica, decimale),
          slicni: formatVrijednost(u.slicni, jedinica, decimale),
          usporedba: usporedba(u, pokazatelj),
        };
      });
    return {
      naziv: grad.naziv,
      tip: tip?.naziv ?? '',
      broj: d.tipovi[grad.tip] ?? 0,
      redovi,
    };
  });

  /** @param {{ tema: import('../state.js').Tema, poStanovniku: boolean }} r */
  function otvori(r) {
    setTema(r.tema);
    setMjera(r.poStanovniku ? 'po-stanovniku' : 'ukupno');
  }
</script>

{#if prikaz}
  <section class="neobicno" aria-labelledby="neobicno-naslov">
    <h3 id="neobicno-naslov">{t('Što je neobično ovdje', 'What stands out here')}</h3>
    <p class="podnaslov">
      {t(
        `U usporedbi s ${prikaz.broj} gradova i općina istog tipa (${prikaz.tip.toLowerCase()}).`,
        `Compared with ${prikaz.broj} cities and municipalities of the same type (${prikaz.tip.toLowerCase()}).`,
      )}
    </p>
    {#if prikaz.redovi.length}
      <ul>
        {#each prikaz.redovi as r (r.kljuc)}
          <li>
            <button
              type="button"
              style:--boja={r.boja}
              title={t(`Prikaži temu ${r.temaNaziv}`, `Show the ${r.temaNaziv} theme`)}
              onclick={() => otvori(r)}
            >
              <span class="naziv">{r.naziv}</span>
              <span class="brojke">
                <strong>{r.vrijednost}</strong> · {r.usporedba}
                <span class="slicni">({t('tipično', 'typically')} {r.slicni})</span>
              </span>
            </button>
          </li>
        {/each}
      </ul>
    {:else}
      <p class="blizu">
        {t(
          `Po pokazateljima koje uspoređujemo ${prikaz.naziv} je blizu sličnih gradova i općina.`,
          `On the indicators we compare, ${prikaz.naziv} is close to similar cities and municipalities.`,
        )}
      </p>
    {/if}
    <p class="napomena">
      {t(
        'Odstupanje nije ocjena: može biti i dobro i loše. Iznosi su po stanovniku.',
        'A difference is not a verdict: it can be good or bad. Amounts are per resident.',
      )}
    </p>
  </section>
{/if}

<style>
  .neobicno {
    margin: 14px 0 0;
    padding-top: 12px;
    border-top: 1px solid var(--kh-rub);
  }

  h3 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
  }

  .podnaslov,
  .blizu,
  .napomena {
    margin: 2px 0 0;
    font-size: 12px;
    line-height: 1.4;
    color: var(--kh-tekst-blago);
  }

  .blizu {
    margin-top: 8px;
    color: var(--kh-tekst);
  }

  .napomena {
    margin-top: 8px;
    font-size: 11.5px;
  }

  ul {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
    display: grid;
    gap: 6px;
  }

  button {
    display: grid;
    gap: 2px;
    width: 100%;
    padding: 7px 10px;
    border: 0;
    border-left: 3px solid var(--boja, var(--kh-naglasak));
    border-radius: 0 6px 6px 0;
    background: var(--kh-pozadina-blaga);
    color: var(--kh-tekst);
    font: inherit;
    font-size: 12.5px;
    line-height: 1.4;
    text-align: left;
    cursor: pointer;
  }

  button:hover {
    filter: brightness(1.15);
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }

  .naziv {
    font-weight: 600;
  }

  .slicni {
    color: var(--kh-tekst-blago);
  }
</style>
