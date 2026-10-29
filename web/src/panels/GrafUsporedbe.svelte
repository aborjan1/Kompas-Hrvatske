<script>
  // Where the selected county stands among all 21 on the indicator the map colours at
  // country level: one bar per county, largest first. Clicking a bar selects that county.
  import { selectArea, view } from '../state.js';
  import { ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { JEDNOSTAVNI_NAZIVI, TEME_POKAZATELJI } from '../data/teme.js';
  import GrafStupci from './GrafStupci.svelte';

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
        id: z.sifra,
        oznaka: z.naziv.replace(/ županija$/, ''),
        naziv: z.naziv,
        value: o.value,
        tekst: formatVrijednost(o.value, o.jedinica, o.decimale),
      });
    }
    redovi.sort((a, b) => b.value - a.value);
    redovi.forEach((r, i) => (r.detalji = [`${i + 1}. mjesto: ${r.tekst}`]));
    const indeks = redovi.findIndex((r) => r.id === v.podrucje);

    return {
      naslov: (JEDNOSTAVNI_NAZIVI[kljuc] ?? pokazatelj.naziv) + (poStanovniku ? ' po stanovniku' : ''),
      godina: pokazatelj.godina,
      redovi,
      odabrani: indeks >= 0 ? redovi[indeks] : null,
      mjesto: indeks + 1,
      ukupno: Object.keys(p.zupanije).length,
      bezPodatka,
      boja: TEME_POKAZATELJI[v.tema].boje[3],
    };
  });
</script>

{#if usporedba}
  <section class="graf" aria-labelledby="graf-zupanije-naslov">
    <h3 id="graf-zupanije-naslov">
      {usporedba.naslov} <span class="godina">{usporedba.godina}</span>
    </h3>
    {#if usporedba.odabrani}
      <p class="isticanje">
        <strong>{usporedba.mjesto}. od {usporedba.redovi.length}</strong> · {usporedba.odabrani.tekst}
      </p>
    {:else}
      <p class="isticanje">Za ovu županiju nema podatka.</p>
    {/if}

    <GrafStupci
      redovi={usporedba.redovi}
      odabrani={usporedba.odabrani?.id ?? null}
      boja={usporedba.boja}
      naslov="{usporedba.naslov}, poredak županija"
      onodaberi={(red) => selectArea('zupanija', red.id)}
    />

    {#if usporedba.bezPodatka}
      <p class="napomena">Bez podatka: {usporedba.bezPodatka} od {usporedba.ukupno} županija.</p>
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

  .isticanje {
    margin: 2px 0 6px;
    font-size: 13px;
    color: var(--kh-tekst);
  }

  .napomena {
    margin: 4px 0 0;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }
</style>
