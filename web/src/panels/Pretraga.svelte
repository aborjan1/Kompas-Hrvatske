<script>
  // Search box for counties, cities and municipalities (ARIA combobox). Choosing a
  // result selects that area, so the map flies there and the URL gets a history entry.
  import { selectArea } from '../state.js';
  import { podaci, ucitajJls } from '../data/podaci.js';
  import { napraviIndeks, trazi } from '../data/pretraga.js';

  let upit = $state('');
  let otvoreno = $state(false);
  let aktivni = $state(0);
  /** @type {HTMLInputElement | undefined} */
  let polje = $state();

  // Rebuilt once jls.json arrives; counties only until then.
  const indeks = $derived(napraviIndeks($podaci.zupanije, $podaci.jls));
  const rezultati = $derived(trazi(indeks, upit));
  const prikazi = $derived(otvoreno && rezultati.length > 0);
  const traziSe = $derived(otvoreno && upit.trim().length >= 2);

  function odaberi(rezultat) {
    selectArea(rezultat.razina, rezultat.sifra);
    upit = '';
    otvoreno = false;
    polje?.blur();
  }

  function onkeydown(e) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!rezultati.length) return;
      e.preventDefault();
      otvoreno = true;
      const korak = e.key === 'ArrowDown' ? 1 : -1;
      aktivni = (aktivni + korak + rezultati.length) % rezultati.length;
    } else if (e.key === 'Enter') {
      if (prikazi && rezultati[aktivni]) {
        e.preventDefault();
        odaberi(rezultati[aktivni]);
      }
    } else if (e.key === 'Escape') {
      if (otvoreno && upit) upit = '';
      else polje?.blur();
      otvoreno = false;
    }
  }
</script>

<div class="kh-panel pretraga">
  <input
    bind:this={polje}
    bind:value={upit}
    type="search"
    role="combobox"
    aria-label="Pretraga županija, gradova i općina"
    aria-autocomplete="list"
    aria-controls="pretraga-rezultati"
    aria-expanded={prikazi}
    aria-activedescendant={prikazi ? `pretraga-${aktivni}` : undefined}
    placeholder="Traži županiju, grad ili općinu…"
    autocomplete="off"
    spellcheck="false"
    onfocus={() => {
      ucitajJls();
      otvoreno = true;
    }}
    onblur={() => (otvoreno = false)}
    oninput={() => {
      otvoreno = true;
      aktivni = 0;
    }}
    {onkeydown}
  />

  <ul id="pretraga-rezultati" role="listbox" aria-label="Rezultati pretrage" hidden={!prikazi}>
    {#each rezultati as r, i (r.razina + r.sifra)}
      <!-- Mouse only: the keyboard moves through the list from the input (aria-activedescendant). -->
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <li
        id="pretraga-{i}"
        role="option"
        aria-selected={i === aktivni}
        onmousedown={(e) => e.preventDefault()}
        onclick={() => odaberi(r)}
        onmouseenter={() => (aktivni = i)}
      >
        <span class="naziv">{r.naziv}</span>
        <span class="opis">{r.opis}</span>
      </li>
    {/each}
  </ul>

  {#if traziSe && !rezultati.length}
    <p class="poruka">Nema rezultata.</p>
  {/if}
  {#if traziSe && !$podaci.jls}
    <p class="poruka">Učitavanje gradova i općina…</p>
  {/if}
</div>

<style>
  .pretraga {
    position: relative;
    width: 340px;
    max-width: 100%;
  }

  input {
    box-sizing: border-box;
    width: 100%;
    padding: 8px 12px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: var(--kh-tekst);
    font: inherit;
    font-size: 14px;
  }

  input:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 0;
  }

  /* Drops over the map instead of pushing the panels around. */
  ul {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    max-height: 320px;
    margin: 0;
    padding: 4px;
    overflow-y: auto;
    list-style: none;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  }

  li {
    display: grid;
    padding: 6px 8px;
    border-radius: 6px;
    cursor: pointer;
  }

  li[aria-selected='true'] {
    background: var(--kh-pozadina-blaga);
  }

  .naziv {
    font-size: 14px;
    color: var(--kh-tekst);
  }

  .opis {
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }

  .poruka {
    margin: 0;
    padding: 0 12px 8px;
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }
</style>
