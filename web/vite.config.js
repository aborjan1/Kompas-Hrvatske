import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  // Relative paths, so the same build works on GitHub Pages (/Kompas-Hrvatske/) and locally.
  base: './',
  plugins: [svelte()],
})
