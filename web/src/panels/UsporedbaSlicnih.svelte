<script>
  // A city or municipality next to the 5 closest to it in population (`slicni` in
  // jls.json, from anywhere in Croatia), on the indicator the map colours for cities.
  // Clicking another one selects it, so the map flies to its county.
  import { selectArea, view } from '../state.js';
  import { ocitaj, podaci } from '../data/podaci.js';
  import { formatVrijednost } from '../data/format.js';
  import { t } from '../jezik.js';
  import { TEME_POKAZATELJI, jednostavniNaziv } from '../data/teme.js';
  import GrafStupci from './GrafStupci.svelte';

  const usporedba = $derived.by(() => {
    const p = $podaci;
    const v = $view;
    const grad = v.razina === 'jls' ? p.jls?.[v.podrucje] : null;
    if (!p.meta || !p.zupanije || !grad) return null;
    const kljuc = TEME_POKAZATELJI[v.tema].karta.jls;
    const pokazatelj = kljuc ? p.meta.pokazatelji[kljuc] : null;
    if (!pokazatelj?.razine.includes('jls')) return { bezPokazatelja: true };

    const redovi = [];
    const bezPodatka = [];
    let poStanovniku = false;
    for (const jls of [grad, ...grad.slicni.map((s) => p.jls[s]).filter(Boolean)]) {
      const o = ocitaj(jls, kljuc, pokazatelj, v.mjera);
      poStanovniku = o.poStanovniku;
      if (o.value === null) {
        bezPodatka.push(jls.naziv);
        continue;
      }
      const zupanija = p.zupanije[jls.nadredeno]?.naziv ?? '';
      const stanovnika = jls.pokazatelji.stanovnistvo;
      redovi.push({
        id: jls.sifra,
        oznaka: jls.naziv,
        naziv: `${jls.naziv} (${zupanija})`,
        value: o.value,
        tekst: formatVrijednost(o.value, o.jedinica, o.decimale),
        stanovnika,
      });
    }
    redovi.sort((a, b) => b.value - a.value);
    for (const r of redovi) {
      r.detalji = [r.tekst];
      if (r.stanovnika != null) r.detalji.push(`${formatVrijednost(r.stanovnika, 'osoba', 0)} ${t('stanovnika', 'residents')}`);
    }
    const indeks = redovi.findIndex((r) => r.id === grad.sifra);

    return {
      naslov: jednostavniNaziv(kljuc, pokazatelj) + (poStanovniku ? t(' po stanovniku', ' per resident') : ''),
      godina: pokazatelj.godina,
      naziv: grad.naziv,
      redovi,
      odabrani: indeks >= 0 ? redovi[indeks] : null,
      mjesto: indeks + 1,
      bezPodatka,
      boja: TEME_POKAZATELJI[v.tema].boje[3],
    };
  });
</script>

{#if usporedba}
  <section class="graf" aria-labelledby="graf-slicni-naslov">
    <h3 id="graf-slicni-naslov">{t('Usporedba sa sličnima po broju stanovnika', 'Compared with places of similar size')}</h3>
    {#if usporedba.bezPokazatelja}
      <p class="napomena">{t('Za ovu temu nema podatka po gradovima i općinama.', 'This theme has no data for cities and municipalities.')}</p>
    {:else}
      <p class="pokazatelj">{usporedba.naslov} <span class="godina">{usporedba.godina}</span></p>
      {#if usporedba.odabrani}
        <p class="isticanje">
          <strong>{t(`${usporedba.mjesto}. od ${usporedba.redovi.length}`, `${usporedba.mjesto} of ${usporedba.redovi.length}`)}</strong> · {usporedba.odabrani.tekst}
        </p>
      {:else}
        <p class="isticanje">{t(`Za ${usporedba.naziv} nema podatka.`, `No data for ${usporedba.naziv}.`)}</p>
      {/if}

      <GrafStupci
        redovi={usporedba.redovi}
        odabrani={usporedba.odabrani?.id ?? null}
        boja={usporedba.boja}
        naslov={t(
          `${usporedba.naslov}: ${usporedba.naziv} i 5 sličnih po broju stanovnika`,
          `${usporedba.naslov}: ${usporedba.naziv} and 5 places of similar size`,
        )}
        visinaRetka={22}
        onodaberi={(red) => selectArea('jls', red.id)}
      />

      {#if usporedba.bezPodatka.length}
        <p class="napomena">{t('Bez podatka', 'No data')}: {usporedba.bezPodatka.join(', ')}.</p>
      {/if}
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

  .pokazatelj {
    margin: 2px 0 0;
    font-size: 12px;
    color: var(--kh-tekst);
  }

  .godina {
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
