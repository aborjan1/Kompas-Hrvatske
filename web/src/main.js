import { mount } from 'svelte'
import './app.css'
import './raspored.css'
import App from './App.svelte'
import { startUrlSync } from './url.js'
import { bezZumaStranice } from './bezZumaStranice.js'

// Before mounting, so the app starts on the view in the link.
startUrlSync()
bezZumaStranice()

// Long-lived cache for map tiles (public/sw.js). Not in dev, where it would hide changes.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`)
}

const app = mount(App, {
  target: document.getElementById('app'),
})

export default app
