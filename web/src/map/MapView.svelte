<script>
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { indicator } from '../data/indicator.js';
  import { odabir } from '../data/podaci.js';
  import { selectArea, view } from '../state.js';
  import {
    COUNTY_BOUNDARIES_URL,
    CROATIA_BOUNDS,
    FOCUS_PADDING,
    INTRO_DURATION,
  } from './config.js';
  import { createCountyLayer, FILL_LAYER, SOURCE } from './countyLayer.js';
  import { createMap, lockToArea, lockToCroatia, setUserInput, unlockCamera } from './createMap.js';
  import { formatNumber } from './format.js';
  import { addHoverTooltip } from './hover.js';
  import { convexHull, simplifiedOutline } from './geometry.js';
  import { hidePlacesOutside } from './labels.js';
  import { createJlsLayer, JLS_FILL_LAYER, JLS_SOURCE } from './jlsLayer.js';
  import { LegendControl } from './legend.js';

  let container;

  onMount(() => {
    const map = createMap(container);
    const legend = new LegendControl();
    map.addControl(legend, 'bottom-left');

    /** @type {import('../data/indicator.js').Indicator | null} */
    let shown = null;
    /** @type {import('../data/indicator.js').Indicator | null} */
    let shownJls = null;
    let unsubscribe = () => {};
    let unsubscribeView = () => {};
    let unsubscribeJls = () => {};

    map.on('load', async () => {
      const response = await fetch(COUNTY_BOUNDARIES_URL);
      if (!response.ok) throw new Error(`${COUNTY_BOUNDARIES_URL}: HTTP ${response.status}`);
      const geojson = await response.json();
      const counties = createCountyLayer(map, geojson);
      const outline = simplifiedOutline(geojson);
      hidePlacesOutside(map, outline);
      const jls = createJlsLayer(map);

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
        legend.update({ title: ind?.title ?? '', unit: ind?.unit, ...legendData });
        colouredLevel = ind?.razina ?? null;
        showColouredAreas();
      });

      // The map only reports the click; the camera moves below, when the state changes,
      // so the breadcrumb, search and URL move it the same way.
      map.on('click', FILL_LAYER, (e) => {
        // Inside the open county the click belongs to its city or municipality.
        if (map.queryRenderedFeatures(e.point, { layers: [JLS_FILL_LAYER] }).length) return;
        selectArea('zupanija', e.features[0].properties.sifra);
      });
      map.on('click', JLS_FILL_LAYER, (e) => selectArea('jls', e.features[0].properties.sifra));

      // Start the intro only once the globe is drawn, not over a blank sphere.
      await new Promise((resolve) => map.once('idle', resolve));

      const hull = convexHull(outline.coordinates.flat(2));
      let focusToken = 0;

      // Flies to an area and, once there, keeps the camera on it: the user can look
      // around inside it but not pan away or zoom out past it. The whole country keeps
      // its own lock (lockToCroatia).
      function focusOn(bounds, { croatia = false, intro = false } = {}) {
        const token = ++focusToken;
        unlockCamera(map);
        // A scroll or drag mid-flight would cancel it before the lock applies and leave
        // the camera free to zoom out to space, so input waits for the landing.
        setUserInput(map, false);
        // moveend also fires when a newer focusOn() interrupts this move; that one
        // locks instead.
        const arrived = () => {
          map.off('moveend', arrived);
          if (token !== focusToken) return;
          if (croatia) lockToCroatia(map, hull);
          else lockToArea(map, bounds);
          setUserInput(map, true);
        };
        // Listen first: under prefers-reduced-motion the move is a jump, whose moveend
        // fires inside fitBounds().
        map.on('moveend', arrived);
        // Not `essential`, so MapLibre jumps instead of flying under prefers-reduced-motion.
        map.fitBounds(bounds, {
          padding: FOCUS_PADDING,
          pitch: map.getPitch(),
          ...(intro && { duration: INTRO_DURATION }),
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
        yieldTo: [JLS_FILL_LAYER],
        describe: (f) => ({
          title: f.properties.naziv,
          detail: Number.isFinite(f.state.value)
            ? `${formatNumber(f.state.value)} ${shown.unit}`
            : 'nema podatka',
        }),
      });
      addHoverTooltip(map, {
        layerId: JLS_FILL_LAYER,
        source: JLS_SOURCE,
        describe: (f) => ({
          title: f.properties.naziv,
          detail:
            !shownJls ? 'nema podatka za ovu temu'
            : Number.isFinite(f.state.value) ? `${formatNumber(f.state.value)} ${shownJls.unit}`
            : 'nema podatka',
        }),
      });
    });

    return () => {
      unsubscribe();
      unsubscribeView();
      unsubscribeJls();
      map.remove();
    };
  });
</script>

<div class="map" bind:this={container}></div>

<style>
  .map {
    position: absolute;
    inset: 0;
    /* Space behind the globe. */
    background: #0b1222;
  }
</style>
