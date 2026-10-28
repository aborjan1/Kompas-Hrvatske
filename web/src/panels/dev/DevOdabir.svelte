<script>
  // DEV ONLY: picks an area until clicks on the map write to the shared state.
  // Rendered only under `npm run dev`; delete once the map's selectArea is wired.
  import { selectArea, view } from '../../state.js';
  import { podaci } from '../../data/podaci.js';

  const zupanije = $derived(
    Object.values($podaci.zupanije ?? {}).sort((a, b) => a.sifra.localeCompare(b.sifra)),
  );

  const sifraZupanije = $derived(
    $view.razina === 'zupanija' ? $view.podrucje : ($podaci.jls?.[$view.podrucje]?.nadredeno ?? ''),
  );

  const jlsZupanije = $derived(
    Object.values($podaci.jls ?? {})
      .filter((j) => j.nadredeno === sifraZupanije)
      .sort((a, b) => a.naziv.localeCompare(b.naziv, 'hr')),
  );

  function odaberiZupaniju(e) {
    const sifra = e.currentTarget.value;
    sifra ? selectArea('zupanija', sifra) : selectArea('drzava');
  }

  function odaberiJls(e) {
    const sifra = e.currentTarget.value;
    sifra ? selectArea('jls', sifra) : selectArea('zupanija', sifraZupanije);
  }
</script>

<div class="kh-panel dev">
  <span class="oznaka">DEV</span>
  <select aria-label="Županija" value={sifraZupanije} onchange={odaberiZupaniju}>
    <option value="">— Hrvatska —</option>
    {#each zupanije as z (z.sifra)}<option value={z.sifra}>{z.sifra} {z.naziv}</option>{/each}
  </select>
  {#if sifraZupanije}
    <select
      aria-label="Grad ili općina"
      value={$view.razina === 'jls' ? $view.podrucje : ''}
      onchange={odaberiJls}
    >
      <option value="">— cijela županija —</option>
      {#each jlsZupanije as j (j.sifra)}<option value={j.sifra}>{j.naziv}</option>{/each}
    </select>
    {#if $podaci.jls && !jlsZupanije.length}<small>nema JLS u mocku</small>{/if}
  {/if}
</div>

<style>
  .dev {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    border: 1px dashed #c47f00;
    font-size: 12px;
  }

  .oznaka {
    font-weight: 700;
    color: #c47f00;
  }

  select {
    max-width: 220px;
    font: inherit;
  }

  small {
    color: var(--kh-tekst-blago);
  }
</style>
