<script>
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { euProjekti } from '../data/euProjekti.js';
  import { GRADOVI, ukljuceniFiltri } from '../data/gradskiPrikaz.js';
  import { indicator } from '../data/indicator.js';
  import { odabir, podaci } from '../data/podaci.js';
  import { selectArea, view } from '../state.js';
  import {
    CITY_MAX_ZOOM,
    COUNTY_BOUNDARIES_URL,
    SPACE_MASK_URL,
    CROATIA_BOUNDS,
    FOCUS_PADDING,
    INTRO_DURATION,
    MAX_ZOOM,
  } from './config.js';
  import { createCountyLayer, FILL_LAYER, SOURCE } from './countyLayer.js';
  import {
    createMap,
    lockToArea,
    lockToCroatia,
    setDataAttribution,
    setUserInput,
    unlockCamera,
  } from './createMap.js';
  import { datumPreuzimanja } from '../data/indicator.js';
  import { brojProjekata, formatVrijednost } from '../data/format.js';
  import { CITY_AREA_LAYERS, CITY_POINT_LAYERS, createCityLayers } from './cityLayers.js';
  import { createEuLayer, EU_LAYER, EU_SOURCE } from './euLayer.js';
  import { addHoverTooltip } from './hover.js';
  import { simplifiedOutline } from './geometry.js';
  import { hidePlacesOutside } from './labels.js';
  import { createJlsLayer, JLS_FILL_LAYER, JLS_SOURCE } from './jlsLayer.js';
  import { LegendControl } from './legend.js';
  import { createSpaceMask } from './spaceMask.js';
  import { shouldWarmUp, warmUp } from './warmUp.js';

  let container;
  // The intro flight from space can be skipped (button or Esc); under
  // prefers-reduced-motion it is a jump anyway, so the button never shows.
  let introRunning = false;

  // A layout with a docked column (src/dizajn.css) covers part of the map; it says how
  // much in --kh-karta-lijevo / --kh-karta-desno, so areas land in the free part.
  function focusPadding() {
    const style = getComputedStyle(document.documentElement);
    const side = (name) => parseFloat(style.getPropertyValue(name)) || 0;
    return {
      top: FOCUS_PADDING,
      bottom: FOCUS_PADDING,
      left: FOCUS_PADDING + side('--kh-karta-lijevo'),
      right: FOCUS_PADDING + side('--kh-karta-desno'),
    };
  }
  let skipIntro = () => {};
  // Frames the current area again, e.g. when a docked column opens or closes
  // ('kh:raspored' from Paneli.svelte) and the free part of the map changes.
  let refocus = () => {};

  // Legend rows carry short units ("563 mil. €", "3,3 %"); a long one such as
  // "na 1.000 stanovnika" or "po stanovniku" goes once into the title instead.
  // The legend has room for one sentence of the explanation; the panel shows all of it.
  // A full stop only ends a sentence before a capital, so "2021. do 2025." stays whole.
  /** @param {string} tekst */
  function prvaRecenica(tekst) {
    const m = tekst.match(/^.+?\.(?=\s+[A-ZČĆŠĐŽ])/);
    return m ? m[0] : tekst;
  }

  /** @param {import('../data/indicator.js').Indicator | null} ind */
  function legendText(ind) {
    if (!ind) return { title: '' };
    const eur = ind.unit.startsWith('EUR');
    const short = eur || ['%', 'osoba', 'broj', 'godina'].includes(ind.unit);
    const rowUnit = eur ? 'EUR' : short ? ind.unit : 'broj';
    const titleUnit = eur ? ind.unit.slice(3) : short ? '' : ` (${ind.unit})`;
    return {
      title: `${ind.title}${titleUnit}`,
      opis: prvaRecenica(ind.objasnjenje),
      format: (/** @type {number} */ v) => formatVrijednost(v, rowUnit, ind.decimale),
    };
  }

  onMount(() => {
    const map = createMap(container);
    const legend = new LegendControl();
    map.addControl(legend, 'bottom-left');
    const onLayout = () => refocus();
    addEventListener('kh:raspored', onLayout);

    /** @type {import('../data/indicator.js').Indicator | null} */
    let shown = null;
    /** @type {import('../data/indicator.js').Indicator | null} */
    let shownJls = null;
    let unsubscribe = () => {};
    let unsubscribeView = () => {};
    let unsubscribeJls = () => {};
    let unsubscribeEu = () => {};
    let unsubscribeCity = () => {};

    // Boundaries: Državna geodetska uprava under the Open Licence (source, date, licence).
    let granicePripisane = false;
    const unsubscribeMeta = podaci.subscribe((p) => {
      const izvor = p.meta?.izvori['granice-upravne-jedinice'];
      if (!izvor || granicePripisane) return;
      granicePripisane = true;
      const datum = datumPreuzimanja(izvor);
      setDataAttribution(
        map,
        `Granice: <a href="${izvor.poveznica}" target="_blank" rel="noopener">${izvor.izdavatelj}</a>` +
          `${datum ? `, preuzeto ${datum}` : ''}, ` +
          '<a href="https://data.gov.hr/otvorena-dozvola" target="_blank" rel="noopener">Otvorena dozvola</a>',
      );
    });

    map.on('load', async () => {
      // Runs alongside the intro; ?zagrij only.
      if (shouldWarmUp()) warmUp(map);
      const response = await fetch(COUNTY_BOUNDARIES_URL);
      if (!response.ok) throw new Error(`${COUNTY_BOUNDARIES_URL}: HTTP ${response.status}`);
      const geojson = await response.json();
      const counties = createCountyLayer(map, geojson);
      const outline = simplifiedOutline(geojson);
      hidePlacesOutside(map, outline);
      const jls = createJlsLayer(map);
      // Everything outside Croatia turns to space once the intro lands (focusOn below).
      const space = await fetch(SPACE_MASK_URL)
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${SPACE_MASK_URL}: HTTP ${r.status}`))))
        .then((mask) => createSpaceMask(map, mask))
        .catch((error) => {
          // Without the outline the map simply keeps its neighbours.
          console.error(error);
          return null;
        });
      const eu = createEuLayer(map);
      unsubscribeEu = euProjekti.subscribe(({ prikazano, poJls }) => {
        if (prikazano && poJls) eu.show(Object.values(poJls));
        else eu.hide();
      });

      // Selecting Zagreb or Rijeka opens its city view: the satellite photo fades in under
      // the switched-on filters, and the camera may zoom in a little further.
      const city = createCityLayers(map);
      // Raised as soon as a city opens; lowered only once the camera has left it
      // (focusOn), since lowering it first would snap the camera out.
      let maxZoom = MAX_ZOOM;
      const showCity = () => {
        const { razina, podrucje } = get(view);
        const grad = razina === 'jls' ? GRADOVI[podrucje] : undefined;
        maxZoom = grad ? CITY_MAX_ZOOM : MAX_ZOOM;
        if (grad) map.setMaxZoom(CITY_MAX_ZOOM);
        city.show(grad?.mapa ?? null, grad ? grad.filtri.filter((f) => get(ukljuceniFiltri).has(f)) : []);
      };
      const unsubscribeCityView = view.subscribe(showCity);
      const unsubscribeFilters = ukljuceniFiltri.subscribe(showCity);
      unsubscribeCity = () => {
        unsubscribeCityView();
        unsubscribeFilters();
      };

      // Which areas show colour: every county for the country; for a county its cities
      // and municipalities (the JLS layer), or the county itself when the tema has
      // nothing for them; for a city or municipality only that one (the JLS layer).
      let area = { razina: 'drzava', podrucje: null };
      let colouredLevel = null;
      function showColouredAreas() {
        const { razina, podrucje } = area;
        counties.showOnly(
          razina === 'drzava' ? null
          : razina === 'zupanija' && colouredLevel === 'zupanija' ? [podrucje]
          : [],
        );
      }

      unsubscribe = indicator.subscribe((ind) => {
        // The legend follows whichever level carries the colours: counties for the
        // country, cities and municipalities inside a county.
        let legendData;
        if (ind?.razina === 'jls') {
          shownJls = ind;
          legendData = jls.setValues(ind.values, ind.boje);
        } else if (ind || get(view).razina !== 'jls') {
          shown = ind;
          legendData = counties.setValues(ind?.values ?? {}, ind?.boje);
        } else {
          // A city or municipality, but the tema has nothing at that level.
          shownJls = null;
          legendData = jls.clearValues();
        }
        legend.update({ ...legendText(ind), ...legendData });
        colouredLevel = ind?.razina ?? null;
        showColouredAreas();
      });

      // The map only reports the click; the camera moves below, when the state changes,
      // so the breadcrumb, search and URL move it the same way.
      // Every layer fires for the same click, so the one on top claims it: an EU
      // circle, then a city or municipality inside the open county, then the county.
      const claimedBy = (point, layers) => map.queryRenderedFeatures(point, { layers }).length > 0;
      map.on('click', FILL_LAYER, (e) => {
        if (claimedBy(e.point, [EU_LAYER, JLS_FILL_LAYER])) return;
        selectArea('zupanija', e.features[0].properties.sifra);
      });
      map.on('click', JLS_FILL_LAYER, (e) => {
        if (claimedBy(e.point, [EU_LAYER])) return;
        selectArea('jls', e.features[0].properties.sifra);
      });
      map.on('click', EU_LAYER, (e) => selectArea('jls', e.features[0].properties.sifra));

      // Scrolling out past a county's or city's framed view goes up a level (city →
      // county → country), like the breadcrumb. A little extra scroll is needed first,
      // so a trackpad's leftover momentum after landing doesn't trigger it.
      const PULL_TO_LEAVE = 150;
      let pull = 0;
      map.on('wheel', ({ originalEvent }) => {
        const atFurthest = map.getZoom() <= map.getMinZoom() + 0.01;
        if (!map.scrollZoom.isEnabled() || !atFurthest || originalEvent.deltaY <= 0) {
          pull = 0;
          return;
        }
        pull += originalEvent.deltaY;
        if (pull < PULL_TO_LEAVE) return;
        pull = 0;
        const { razina, zupanija } = get(odabir);
        if (razina === 'jls' && zupanija) selectArea('zupanija', zupanija);
        else if (razina !== 'drzava') selectArea('drzava');
      });

      // Start the intro only once the globe is drawn, not over a blank sphere.
      await new Promise((resolve) => map.once('idle', resolve));

      let focusToken = 0;

      // Flies to an area and, once there, keeps the camera on it: the user can look
      // around inside it but not pan away or zoom out past it. The whole country keeps
      // its own lock (lockToCroatia).
      function focusOn(bounds, { croatia = false, intro = false, duration = undefined } = {}) {
        const token = ++focusToken;
        // End a flight still under way before listening below: its moveend would
        // otherwise count as this move's landing and lock the camera mid-air.
        map.stop();
        introRunning = intro;
        // „Preskoči”: the same landing as the intro's, without the flight.
        skipIntro = () => focusOn(bounds, { croatia, duration: 0 });
        refocus = () => focusOn(bounds, { croatia });
        unlockCamera(map);
        // A scroll or drag mid-flight would cancel it before the lock applies and leave
        // the camera free to zoom out to space, so input waits for the landing.
        setUserInput(map, false);
        // moveend also fires when a newer focusOn() interrupts this move; that one
        // locks instead.
        const arrived = () => {
          map.off('moveend', arrived);
          if (token !== focusToken) return;
          introRunning = false;
          space?.show();
          map.setMaxZoom(maxZoom);
          if (croatia) lockToCroatia(map);
          else lockToArea(map, bounds);
          setUserInput(map, true);
        };
        // Listen first: under prefers-reduced-motion the move is a jump, whose moveend
        // fires inside fitBounds().
        map.on('moveend', arrived);
        // Not `essential`, so Mapbox jumps instead of flying under prefers-reduced-motion.
        map.fitBounds(bounds, {
          padding: focusPadding(),
          pitch: map.getPitch(),
          ...(intro && { duration: INTRO_DURATION }),
          ...(duration !== undefined && { duration }),
        });
      }

      // The first call is the intro: from the globe (createMap) straight down to the
      // current area, which is the whole country unless the app opened on a county.
      let focused = null;
      unsubscribeView = view.subscribe(({ razina, podrucje }) => {
        const key = `${razina}/${podrucje}`;
        if (key === focused) return;
        const intro = focused === null;
        focused = key;
        const countyBounds = razina === 'zupanija' && counties.bounds(podrucje);
        if (countyBounds) focusOn(countyBounds, { intro });
        // A city or municipality is framed below, once its county is known; the intro
        // then lands on the whole country first.
        else if (razina === 'drzava' || intro) focusOn(CROATIA_BOUNDS, { croatia: true, intro });
      });

      // The open county's cities and municipalities, and the selected one framed.
      // Follows `odabir` rather than `view` because a JLS's county is only known once
      // jls.json has loaded.
      let shownArea = null;
      unsubscribeJls = odabir.subscribe(async ({ razina, podrucje, zupanija }) => {
        const selected = razina === 'jls' ? podrucje : null;
        const key = `${razina}/${podrucje}/${zupanija}`;
        if (key === shownArea) return;
        shownArea = key;
        area = { razina, podrucje };
        showColouredAreas();
        if (!zupanija) return jls.hide();

        try {
          await jls.showCounty(zupanija);
        } catch (error) {
          console.error(error);
          return;
        }
        if (key !== shownArea) return;
        jls.select(selected);
        const bounds = selected && jls.bounds(selected);
        if (bounds) focusOn(bounds);
      });

      addHoverTooltip(map, {
        layerId: FILL_LAYER,
        source: SOURCE,
        yieldTo: [...CITY_POINT_LAYERS, ...CITY_AREA_LAYERS, EU_LAYER, JLS_FILL_LAYER],
        describe: (f) => ({
          title: f.properties.naziv,
          detail: Number.isFinite(f.state.value)
            ? formatVrijednost(f.state.value, shown.unit, shown.decimale)
            : 'nema podatka',
        }),
      });
      addHoverTooltip(map, {
        layerId: JLS_FILL_LAYER,
        source: JLS_SOURCE,
        yieldTo: [...CITY_POINT_LAYERS, ...CITY_AREA_LAYERS, EU_LAYER],
        describe: (f) => ({
          title: f.properties.naziv,
          detail:
            !shownJls ? 'nema podatka za ovu temu'
            : Number.isFinite(f.state.value) ? formatVrijednost(f.state.value, shownJls.unit, shownJls.decimale)
            : 'nema podatka',
        }),
      });
      addHoverTooltip(map, {
        layerId: EU_LAYER,
        source: EU_SOURCE,
        describe: (f) => ({
          title: `${f.properties.mjesto}: EU projekti`,
          detail: `${brojProjekata(f.properties.broj)} · ${formatVrijednost(f.properties.esif_eur, 'EUR', 0)}`,
        }),
      });

      // City view: one tooltip per layer, points before areas.
      const m2 = (v) => formatVrijednost(v, 'm²', 0);
      const cityTooltips = {
        'grad-ulaganja': (p) => ({ title: p.naziv, detail: `${formatVrijednost(p.iznos, 'EUR', 0)} · plan ${p.godina}.` }),
        'grad-prostori': (p) => ({
          title: p.adresa,
          detail: p.zakupnina_mjesecno != null
            ? `${p.djelatnost} · ${m2(p.povrsina)} · ${formatVrijednost(p.zakupnina_mjesecno, 'EUR', 0)} mjesečno`
            : `Prazno: ${p.vrsta} · ${m2(p.povrsina)}`,
        }),
        'grad-trznice': (p) => ({ title: p.naziv, detail: 'Gradska tržnica' }),
        'grad-drustva': (p) => ({ title: p.naziv, detail: `Gradsko društvo · ${p.udjeli}` }),
        'grad-brownfield-fill': (p) => ({ title: p.naziv, detail: `Napuštena površina · ${formatVrijednost(p.povrsina_ha, 'ha', 1)}` }),
        'grad-zone-fill': (p) => ({
          title: p.namjena || p.vrsta,
          detail: `${p.vrsta} zona · ${formatVrijednost(p.povrsina_ha, 'ha', 1)}${p.izgradjenost === 'neizgrađeno' ? ' · neizgrađeno' : ''}`,
        }),
        'grad-cetvrti-fill': (p, state) => ({
          title: p.naziv,
          detail: Number.isFinite(state.value) ? `Gospodarske površine: ${formatVrijednost(state.value, '%', 1)}` : 'nema podatka',
        }),
      };
      const cityLayers = [...CITY_POINT_LAYERS, ...CITY_AREA_LAYERS];
      cityLayers.forEach((layerId, i) => {
        addHoverTooltip(map, {
          layerId,
          source: map.getLayer(layerId).source,
          yieldTo: cityLayers.slice(0, i),
          describe: (f) => cityTooltips[layerId](f.properties, f.state),
        });
      });
    });

    return () => {
      unsubscribe();
      unsubscribeView();
      unsubscribeJls();
      unsubscribeEu();
      unsubscribeCity();
      unsubscribeMeta();
      removeEventListener('kh:raspored', onLayout);
      map.remove();
    };
  });
</script>

<svelte:window onkeydown={(e) => introRunning && e.key === 'Escape' && skipIntro()} />

<div class="map" bind:this={container}></div>
{#if introRunning}
  <button type="button" class="kh-panel preskoci" onclick={() => skipIntro()}>Preskoči uvod ›</button>
{/if}

<style>
  .preskoci {
    position: absolute;
    right: 16px;
    bottom: 40px;
    padding: 8px 14px;
    border: 0;
    font: 14px system-ui, sans-serif;
    color: var(--kh-tekst);
    cursor: pointer;
  }

  .preskoci:hover {
    background: #fff;
  }

  .preskoci:focus-visible {
    outline: 2px solid var(--kh-naglasak);
    outline-offset: 2px;
  }

  .map {
    position: absolute;
    inset: 0;
    /* Space behind the globe. */
    background: #0b1222;
  }
</style>
