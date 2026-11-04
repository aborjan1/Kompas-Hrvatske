<script>
  // "EU calls for you": planned and open EU calls for 2026 in which the selected city,
  // municipality or county can take part (eu-pozivi.json), and how much similar
  // municipalities have already contracted from EU funds 2021–2027 (jls.json).
  import { view } from '../state.js';
  import { nadjiPodrucje, podaci } from '../data/podaci.js';
  import { euPozivi, stanje, ucitajEuPozive } from '../data/euPozivi.js';
  import { formatVrijednost } from '../data/format.js';
  import { TEME_POKAZATELJI } from '../data/teme.js';
  import { engleski, t } from '../jezik.js';

  $effect(() => ucitajEuPozive());

  const ULOGA = { prijavitelj: t('kao prijavitelj', 'as applicant'), partner: t('kao partner', 'as partner') };

  const podrucje = $derived(nadjiPodrucje($podaci, $view.razina, $view.podrucje));

  const prikaz = $derived.by(() => {
    const d = $euPozivi.podaci;
    if (!d || !podrucje || $view.razina === 'drzava') return null;
    const jls = $view.razina === 'jls';
    const zup = jls ? podrucje.nadredeno : podrucje.sifra;
    const uPodrucju = (p) => p.zupanije === null || p.zupanije.includes(zup);

    const pozivi = d.pozivi
      .map((p) => {
        const imenovan = jls && p.imenovani.includes(podrucje.sifra);
        const uloga = jls ? p.jls : p.zupanija;
        if (!imenovan && !(uloga && uPodrucju(p))) return null;
        // A call only for named cities, or for the area around one, shows only there.
        if (!imenovan && jls && p.imenovani.length && !p.napomena) return null;
        const s = stanje(p);
        if (s.kod === 'zatvoren') return null;
        return {
          ...p,
          stanje: s,
          uloga: imenovan ? t('namijenjen ovom gradu', 'meant for this town') : ULOGA[uloga],
          iznosTekst: p.iznos ? formatVrijednost(p.iznos, 'EUR', 0) : null,
        };
      })
      .filter(Boolean);

    // How the area compares with similar ones on EU money already contracted (2021–2027).
    let usporedba = null;
    if (jls && $podaci.jls && podrucje.slicni_profil?.length) {
      const poSt = (j) => j?.po_stanovniku?.eu_2127_ugovoreno;
      const vrijednosti = podrucje.slicni_profil.map((s) => poSt($podaci.jls[s])).filter((v) => v != null).sort((a, b) => a - b);
      const ovdje = poSt(podrucje);
      if (vrijednosti.length && ovdje != null) {
        const medijan = vrijednosti[Math.floor(vrijednosti.length / 2)];
        usporedba = {
          slicni: formatVrijednost(medijan, 'EUR po stanovniku', 0),
          ovdje: formatVrijednost(ovdje, 'EUR po stanovniku', 0),
          manje: ovdje < medijan * 0.75,
        };
      }
    }
    return {
      pozivi,
      usporedba,
      naziv: podrucje.naziv,
      jls,
      napomena: d.napomena,
      boja: TEME_POKAZATELJI[$view.tema].boje[3],
    };
  });

  // The list can run to 15 calls, so it starts short. Remembered per area: the next
  // area starts short again.
  const PRVIH = 3;
  /** @type {string | null} */
  let sveZa = $state(null);
  const vidljivi = $derived(
    !prikaz ? [] : sveZa === podrucje?.sifra ? prikaz.pozivi : prikaz.pozivi.slice(0, PRVIH),
  );
</script>

{#if prikaz}
  <section class="graf" aria-labelledby="eu-pozivi-naslov">
    <h3 id="eu-pozivi-naslov">
      {prikaz.jls ? t('EU pozivi za grad ili općinu', 'EU calls for this city or municipality') : t('EU pozivi za županiju', 'EU calls for this county')}
      <span class="godina">{t('2026.', '2026')}</span>
    </h3>
    {#if prikaz.usporedba}
      <p class="usporedba" class:upozorenje={prikaz.usporedba.manje}>
        {#if engleski()}
          Similar cities and municipalities (by profile) have contracted on average
          <strong>{prikaz.usporedba.slicni}</strong> from EU funds 2021–2027, and {prikaz.naziv}
          <strong>{prikaz.usporedba.ovdje}</strong>.
        {:else}
          Slični gradovi i općine (po profilu) ugovorili su iz EU fondova 2021.–2027. u prosjeku
          <strong>{prikaz.usporedba.slicni}</strong>, a {prikaz.naziv} <strong>{prikaz.usporedba.ovdje}</strong>.
        {/if}
      </p>
    {/if}
    {#if prikaz.pozivi.length}
      <p class="podnaslov">
        {#if engleski()}
          {prikaz.pozivi.length}
          {prikaz.pozivi.length === 1 ? 'open or planned call' : 'open or planned calls'} the
          {prikaz.jls ? 'city or municipality' : 'county'} can take part in:
        {:else}
          {prikaz.pozivi.length}
          {prikaz.pozivi.length === 1 ? 'otvoren ili planiran poziv' : 'otvorenih ili planiranih poziva'} u kojima
          {prikaz.jls ? 'grad ili općina može' : 'županija može'} sudjelovati:
        {/if}
      </p>
      <ul class="popis">
        {#each vidljivi as p (p.id)}
          <li style:--boja={prikaz.boja}>
            <p class="naziv"><span class="program" title={p.program_naziv}>{p.program}</span> {p.naziv}</p>
            <p class="detalji">
              <span class="stanje {p.stanje.kod}">{p.stanje.tekst}</span>
              · {p.uloga}{p.iznosTekst ? ` · ${p.iznosTekst} ${t('za cijeli poziv', 'for the whole call')}` : ''}
            </p>
            {#if p.napomena}<p class="detalji">{p.napomena}</p>{/if}
            <details>
              <summary>{t('Tko se može prijaviti', 'Who can apply')}</summary>
              <p lang="hr">{p.prijavitelji}</p>
              {#if engleski()}<p class="sitno">As written in the plan (in Croatian).</p>{/if}
              <p class="sitno">{p.vrsta} · {t('područje', 'area')}: {p.podrucje}</p>
            </details>
          </li>
        {/each}
      </ul>
      {#if vidljivi.length < prikaz.pozivi.length}
        <button type="button" class="sve" onclick={() => (sveZa = podrucje.sifra)}>
          {t(`Prikaži sve (${prikaz.pozivi.length})`, `Show all (${prikaz.pozivi.length})`)}
        </button>
      {/if}
    {:else}
      <p class="podnaslov">
        {prikaz.jls
          ? t('Trenutno nema otvorenih ni planiranih poziva za gradove i općine na ovom području.', 'There are currently no open or planned calls for cities and municipalities in this area.')
          : t('Trenutno nema otvorenih ni planiranih poziva za županije na ovom području.', 'There are currently no open or planned calls for counties in this area.')}
      </p>
    {/if}
    <p class="napomena">
      {prikaz.napomena}
      {t('Izvor: Ministarstvo regionalnoga razvoja i fondova EU (eufondovi.gov.hr).', 'Source: Ministry of Regional Development and EU Funds (eufondovi.gov.hr).')}
    </p>
  </section>
{/if}

<style>
  .graf {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
  }

  .sve {
    padding: 2px 0;
    border: 0;
    background: none;
    color: var(--kh-naglasak);
    font: inherit;
    font-size: 12px;
    cursor: pointer;
  }

  .sve:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
    border-radius: 3px;
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

  .usporedba {
    margin: 4px 0 6px;
    padding: 6px 8px;
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    font-size: 12px;
    line-height: 1.4;
    color: var(--kh-tekst);
  }

  .usporedba.upozorenje {
    box-shadow: inset 3px 0 0 #e4692f;
  }

  .podnaslov {
    margin: 4px 0;
    font-size: 12px;
    color: var(--kh-tekst);
  }

  .popis {
    display: grid;
    gap: 8px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .popis li {
    padding-left: 8px;
    border-left: 3px solid var(--boja);
  }

  .naziv {
    margin: 0;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
    color: var(--kh-tekst);
  }

  .program {
    display: inline-block;
    padding: 0 4px;
    border-radius: 3px;
    background: var(--kh-pozadina-blaga);
    font-size: 10px;
    font-weight: 700;
    color: var(--kh-tekst-blago);
  }

  .detalji {
    margin: 2px 0 0;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  .stanje.otvoren {
    font-weight: 700;
    color: var(--boja);
  }

  .stanje.uskoro {
    font-weight: 600;
    color: var(--kh-tekst);
  }

  details {
    margin-top: 2px;
    font-size: 11px;
    color: var(--kh-tekst-blago);
  }

  summary {
    cursor: pointer;
    color: var(--kh-naglasak);
  }

  details p {
    margin: 3px 0 0;
    line-height: 1.4;
  }

  .sitno {
    font-size: 10.5px;
  }

  .napomena {
    margin: 8px 0 0;
    font-size: 11px;
    line-height: 1.35;
    color: var(--kh-tekst-blago);
  }
</style>
