// Hover highlight + tooltip for any polygon layer whose source uses promoteId.
// Hover is internal to the map: it never touches shared app state.

import { Popup } from 'maplibre-gl';
import './hover.css';

/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {{ layerId: string, source: string,
 *   describe: (feature: import('maplibre-gl').MapGeoJSONFeature) => { title: string, detail: string },
 *   yieldTo?: string[] }} options `yieldTo`: layers drawn above this one that own the
 *   hover where they have features (a county yields to its cities and municipalities).
 */
export function addHoverTooltip(map, { layerId, source, describe, yieldTo = [] }) {
  const popup = new Popup({
    closeButton: false,
    closeOnClick: false,
    className: 'kh-tooltip',
    offset: 14,
    maxWidth: '260px',
  });
  let hoveredId = null;

  function setHovered(id) {
    if (hoveredId !== null) map.setFeatureState({ source, id: hoveredId }, { hover: false });
    hoveredId = id;
    if (id !== null) map.setFeatureState({ source, id }, { hover: true });
  }

  map.on('mousemove', layerId, (e) => {
    if (yieldTo.length && map.queryRenderedFeatures(e.point, { layers: yieldTo }).length) {
      setHovered(null);
      popup.remove();
      return;
    }
    const feature = e.features[0];
    if (feature.id !== hoveredId) setHovered(feature.id);

    const { title, detail } = describe(feature);
    const content = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = title;
    content.append(strong, document.createElement('br'), detail);

    popup.setLngLat(e.lngLat).setDOMContent(content).addTo(map);
    map.getCanvas().style.cursor = 'pointer';
  });

  map.on('mouseleave', layerId, () => {
    setHovered(null);
    popup.remove();
    map.getCanvas().style.cursor = '';
  });
}
