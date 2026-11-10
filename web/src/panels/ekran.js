// Whether the screen has room for the charts column beside the left one and still shows
// enough map. Below this the charts are a tab of the info panel instead. raspored.css
// uses the same query for the column's rules.

import { readable } from 'svelte/store';

const UPIT = '(min-width: 1100px) and (min-height: 501px)';

/** @type {import('svelte/store').Readable<boolean>} */
export const siroko = readable(false, (set) => {
  if (typeof matchMedia !== 'function') return;
  const mq = matchMedia(UPIT);
  set(mq.matches);
  const promjena = () => set(mq.matches);
  mq.addEventListener('change', promjena);
  return () => mq.removeEventListener('change', promjena);
});
