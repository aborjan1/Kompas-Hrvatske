// Map constants shared by every map module. Coordinates are WGS84 [lng, lat].

// Mapbox "Outdoors": relief, globe and a classic label hierarchy. Free tier: 50,000
// map loads a month with Mapbox GL JS, tiles included; Mapbox logo required.
// The token comes from web/.env.local and ends up in the page anyway, so restrict it
// to our URLs in the Mapbox account.
export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
if (!MAPBOX_TOKEN) console.error('VITE_MAPBOX_TOKEN is missing, see web/README.md');
export const BASEMAP_STYLE = 'mapbox://styles/mapbox/outdoors-v12';

// The map opens on the globe seen from space, then flies to the current area.
export const INTRO_START = { center: [16.4, 44.5], zoom: 1.2 };
export const INTRO_DURATION = 6000;

// Croatia's extent, used for the intro and for "back to country" camera moves.
export const CROATIA_BOUNDS = [
  [13.2, 42.15],
  [19.65, 46.75],
];

// Camera padding around a focused area, equal on all sides so it lands centred.
export const FOCUS_PADDING = 40;

// Furthest in after the intro: a whole city (Zagreb fills the screen). Furthest out is
// the whole-country view, which depends on the screen size (lockToCroatia()).
export const MAX_ZOOM = 10.25;

export const LABEL_LANGUAGE = 'hr';

// Official DGU county boundaries from pipeline/build.py (docs/format-podataka.md).
export const COUNTY_BOUNDARIES_URL = `${import.meta.env.BASE_URL}data/zupanije.geojson`;

// City and municipality boundaries, one file per county.
/** @param {string} countyCode */
export const JLS_BOUNDARIES_URL = (countyCode) =>
  `${import.meta.env.BASE_URL}data/jls/${countyCode}.geojson`;
