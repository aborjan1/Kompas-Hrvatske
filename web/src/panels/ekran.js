// Whether the screen is wide enough for the chart panel in the top-left corner. Below
// this width it would run into the breadcrumb and search in the top centre, so the
// charts move into the info panel instead.

import { readable } from 'svelte/store';

const UPIT = '(min-width: 1100px)';

/** @type {import('svelte/store').Readable<boolean>} */
export const siroko = readable(false, (set) => {
  if (typeof matchMedia !== 'function') return;
  const mq = matchMedia(UPIT);
  set(mq.matches);
  const promjena = () => set(mq.matches);
  mq.addEventListener('change', promjena);
  return () => mq.removeEventListener('change', promjena);
});
