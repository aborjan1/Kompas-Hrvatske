// Map constants shared by every map module. Coordinates are WGS84 [lng, lat].

// OpenFreeMap (OpenStreetMap data), no API key. Positron is the muted light style.
export const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/positron';

// Croatia's extent, used for the initial view and for "back to country" camera moves.
export const CROATIA_BOUNDS = [
  [13.2, 42.15],
  [19.65, 46.75],
];

// Camera padding that keeps the focused area clear of the floating panels
// (src/panels/): the info panel is ~344 px wide on the right, and moves to the
// bottom on screens up to 640 px.
export function focusPadding(width) {
  return width > 640
    ? { top: 40, right: 370, bottom: 80, left: 40 }
    : { top: 70, right: 20, bottom: 260, left: 20 };
}

// Panning limit: Croatia plus a margin so neighbours stay visible for context.
export const MAX_BOUNDS = [
  [9.5, 39.5],
  [23.5, 49.0],
];

export const LABEL_LANGUAGE = 'hr';

// Official DGU county boundaries from pipeline/build.py (docs/format-podataka.md).
export const COUNTY_BOUNDARIES_URL = `${import.meta.env.BASE_URL}data/zupanije.geojson`;
