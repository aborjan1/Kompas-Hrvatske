<script>
  // Breadcrumb: Država → Županija → Grad. Earlier steps are links back up.
  import { selectArea, view } from '../state.js';
  import { podaci } from '../data/podaci.js';

  const koraci = $derived.by(() => {
    const { razina, podrucje } = $view;
    const p = $podaci;
    const jls = razina === 'jls' ? p.jls?.[podrucje] : null;
    const sifraZupanije = razina === 'zupanija' ? podrucje : jls?.nadredeno;

    const lista = [{ naziv: 'Hrvatska', odaberi: () => selectArea('drzava') }];
    if (sifraZupanije) {
      lista.push({
        naziv: p.zupanije?.[sifraZupanije]?.naziv ?? '…',
        odaberi: () => selectArea('zupanija', sifraZupanije),
      });
    }
    if (razina === 'jls') lista.push({ naziv: jls?.naziv ?? '…', odaberi: null });
    return lista;
  });
</script>

<nav class="kh-panel putanja" aria-label="Putanja">
  <ol>
    {#each koraci as korak, i}
      <li>
        {#if i < koraci.length - 1}
          <button type="button" class="link" onclick={korak.odaberi}>{korak.naziv}</button>
          <span class="strelica" aria-hidden="true">›</span>
        {:else}
          <span aria-current="page">{korak.naziv}</span>
        {/if}
      </li>
    {/each}
  </ol>
</nav>

<style>
  .putanja {
    box-sizing: border-box;
    max-width: 100%;
    padding: 8px 12px;
    font-size: 14px;
  }

  ol {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  li {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  [aria-current='page'] {
    font-weight: 600;
    color: var(--kh-tekst);
  }

  .link {
    padding: 0;
    border: 0;
    background: none;
    color: var(--kh-naglasak);
    font: inherit;
    cursor: pointer;
  }

  .link:hover {
    text-decoration: underline;
  }

  .strelica {
    color: var(--kh-tekst-blago);
  }

  /* Phones: one line, so the search box and the legend below stay put. A long county
     name gives way first ("Dubrovačko-neretv…"); "Hrvatska" never shrinks. */
  @media (max-width: 640px) {
    ol {
      flex-wrap: nowrap;
    }

    li {
      min-width: 0;
    }

    li:first-child {
      flex: none;
    }

    .link,
    [aria-current='page'] {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
</style>
