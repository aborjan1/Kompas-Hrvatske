// Map constants shared by every map module. Coordinates are WGS84 [lng, lat].

// OpenFreeMap (OpenStreetMap data), no API key. Positron is the muted light style.
export const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/positron';

// Croatia's extent, used for the initial view and for "back to country" camera moves.
export const CROATIA_BOUNDS = [
  [13.2, 42.15],
  [19.65, 46.75],
];

// Panning limit: Croatia plus a margin so neighbours stay visible for context.
export const MAX_BOUNDS = [
  [9.5, 39.5],
  [23.5, 49.0],
];

export const LABEL_LANGUAGE = 'hr';

// Dev fixture: geoBoundaries HRV ADM1 (ODbL, © OpenStreetMap contributors) with
// `sifra`/`naziv` added.
// TODO(David): waiting on the data contract + sample file. Point this at the
// county GeoJSON in web/public/data/, check the property names, delete dev/.
export { default as COUNTY_BOUNDARIES_URL } from './dev/zupanije.mock.geojson?url';
