<script>
  // The stories on offer, in the country view of the info panel. Choosing one plays it
  // (src/stories/player.js); the card at the bottom takes it from there.
  import { pokreni, price, reprodukcija, tekstPrice } from '../stories/player.js';
  import { t } from '../jezik.js';
</script>

<section class="price" aria-labelledby="price-naslov">
  <h3 id="price-naslov">{t('Priče', 'Stories')}</h3>
  <ul>
    {#each price as prica (prica.id)}
      <li>
        <button
          type="button"
          aria-current={$reprodukcija?.prica.id === prica.id ? 'true' : undefined}
          onclick={() => pokreni(prica.id)}
        >
          <span class="naziv">{tekstPrice(prica).naslov}</span>
          <span class="opis">{tekstPrice(prica).opis} · {prica.scene.length} {t('koraka', 'steps')}</span>
        </button>
      </li>
    {/each}
  </ul>
</section>

<style>
  .price {
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--kh-rub);
  }

  h3 {
    margin: 0 0 6px;
    font-size: 12px;
    font-weight: 600;
    color: var(--kh-tekst);
  }

  ul {
    display: grid;
    gap: 4px;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  button {
    display: grid;
    width: 100%;
    padding: 7px 10px;
    border: 0;
    border-radius: 6px;
    background: var(--kh-pozadina-blaga);
    text-align: left;
    font: inherit;
    cursor: pointer;
  }

  button:hover {
    background: #e4e3de;
  }

  button[aria-current='true'] {
    box-shadow: inset 3px 0 0 var(--kh-naglasak);
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }

  .naziv {
    font-size: 14px;
    color: var(--kh-tekst);
  }

  .opis {
    font-size: 12px;
    color: var(--kh-tekst-blago);
  }
</style>
