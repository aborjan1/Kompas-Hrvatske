import { mount } from 'svelte'
import './app.css'
import './dizajn.css'
import './dizajn-raspored.css'
import App from './App.svelte'
import { startUrlSync } from './url.js'

// Panel design experiment (#79): ?dizajn=staklo|minimal|kartice (colours, dizajn.css)
// or traka|traka2|pucina|prica|hud (layouts, dizajn-raspored.css).
const dizajn = new URLSearchParams(location.search).get('dizajn')
if (dizajn) document.documentElement.dataset.dizajn = dizajn

// Before mounting, so the app starts on the view in the link.
startUrlSync()

// Long-lived cache for map tiles (public/sw.js). Not in dev, where it would hide changes.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`)
}

const app = mount(App, {
  target: document.getElementById('app'),
})

export default app
