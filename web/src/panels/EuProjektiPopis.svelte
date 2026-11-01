<script>
  // EU projects of the selected city or municipality: count, total and the five
  // largest. Shown only while the EU layer is switched on.
  import { view } from '../state.js';
  import { euProjekti } from '../data/euProjekti.js';
  import { brojProjekata, formatVrijednost } from '../data/format.js';

  const jls = $derived($euProjekti.poJls?.[$view.podrucje] ?? null);
</script>

{#if $euProjekti.prikazano}
  <section class="eu">
    <h3>EU projekti 2014.–2020.</h3>
    {#if $euProjekti.greska}
      <p class="blago">{$euProjekti.greska}</p>
    {:else if !$euProjekti.poJls}
      <p class="blago">Učitavanje…</p>
    {:else if !jls}
      <p class="blago">Nema EU projekata u ovom razdoblju.</p>
    {:else}
      <p class="ukupno">
        <strong>{formatVrijednost(jls.esif_eur, 'EUR', 0)}</strong> iz EU · {brojProjekata(jls.broj)}
      </p>
      <ol>
        {#each jls.najveci as p}
          <li>
            <span class="naziv" title={p.naziv}>{p.naziv}</span>
            <span class="blago">{p.korisnik} · {formatVrijednost(p.esif_eur, 'EUR', 0)}</span>
          </li>
        {/each}
      </ol>
      <p class="blago izvor">Stanje {$euProjekti.presjek}</p>
    {/if}
  </section>
{/if}

<style>
  .eu {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
  }

  h3 {
    margin: 0 0 6px;
    font-size: 13px;
    font-weight: 600;
    color: #003399;
  }

  .ukupno {
    margin: 0 0 8px;
    font-size: 14px;
  }

  .ukupno strong {
    font-size: 17px;
  }

  ol {
    display: grid;
    gap: 6px;
    margin: 0;
    padding-left: 18px;
    font-size: 13px;
  }

  li > span {
    display: block;
  }

  /* Project titles can be very long: two lines, the rest on hover. */
  .naziv {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.3;
  }

  .blago {
    margin: 0;
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }

  .izvor {
    margin-top: 8px;
  }
</style>
