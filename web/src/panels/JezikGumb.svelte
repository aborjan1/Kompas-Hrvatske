<script>
  // HR / EN switch next to the breadcrumb (src/jezik.js). The panels are rebuilt in the
  // new language (App.svelte), so focus is put back on the switch afterwards.
  import { jezik, setJezik } from '../jezik.js';

  /** @param {'hr' | 'en'} j */
  function odaberi(j) {
    if (j === $jezik) return;
    setJezik(j);
    setTimeout(() => document.querySelector(`.jezik button[lang="${j}"]`)?.focus());
  }
</script>

<div class="kh-panel jezik" role="group" aria-label={$jezik === 'en' ? 'Language' : 'Jezik'}>
  <button type="button" lang="hr" aria-pressed={$jezik === 'hr'} title="Hrvatski" onclick={() => odaberi('hr')}>HR</button>
  <button type="button" lang="en" aria-pressed={$jezik === 'en'} title="English" onclick={() => odaberi('en')}>EN</button>
</div>

<style>
  .jezik {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 3px;
    flex: none;
  }

  button {
    padding: 4px 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--kh-tekst-blago);
    font: inherit;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    cursor: pointer;
  }

  button:hover {
    color: var(--kh-tekst);
  }

  button[aria-pressed='true'] {
    background: var(--kh-naglasak);
    color: #fff;
  }

  button:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 1px;
  }
</style>
