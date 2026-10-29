// Small planar geometry on [lng, lat] degrees. Precise enough at Croatia's scale for
// label filtering and camera limits; not for measuring distances or areas.

import { LngLatBounds } from 'maplibre-gl';

// ~500 m is precise enough for both uses, and islets this small have no settlement.
const TOLERANCE = 0.005; // degrees
const MIN_RING_AREA = 1e-5; // square degrees, ~0.08 km²

/**
 * Outer rings of all counties, simplified. MapLibre's `within` converts its whole
 * polygon to tile coordinates for every label it tests, so the full boundaries
 * (12k points) made tiles load slowly.
 * @param {GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon>} counties
 * @returns {GeoJSON.MultiPolygon}
 */
export function simplifiedOutline(counties) {
  const rings = counties.features
    .flatMap(({ geometry: g }) => (g.type === 'Polygon' ? [g.coordinates] : g.coordinates))
    .map((polygon) => polygon[0])
    .filter((ring) => ringArea(ring) >= MIN_RING_AREA)
    .map((ring) => simplify(ring, TOLERANCE))
    .filter((ring) => ring.length >= 4);
  return { type: 'MultiPolygon', coordinates: rings.map((ring) => [ring]) };
}

/**
 * Convex hull (Andrew's monotone chain), counter-clockwise and not closed.
 * @param {number[][]} points
 * @returns {number[][]}
 */
export function convexHull(points) {
  const sorted = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const half = (list) => {
    const chain = [];
    for (const p of list) {
      while (chain.length >= 2 && cross(chain[chain.length - 2], chain[chain.length - 1], p) <= 0) {
        chain.pop();
      }
      chain.push(p);
    }
    chain.pop();
    return chain;
  };
  return [...half(sorted), ...half(sorted.reverse())];
}

/**
 * The point itself if it is inside the convex hull, otherwise the nearest point on its edge.
 * @param {number[]} point
 * @param {number[][]} hull From convexHull().
 * @returns {number[]}
 */
export function clampToHull(point, hull) {
  const edges = hull.map((a, i) => [a, hull[(i + 1) % hull.length]]);
  if (edges.every(([a, b]) => cross(a, b, point) >= 0)) return point;

  let nearest = point;
  let best = Infinity;
  for (const [a, b] of edges) {
    const q = closestOnSegment(point, a, b);
    const d = Math.hypot(point[0] - q[0], point[1] - q[1]);
    if (d < best) [best, nearest] = [d, q];
  }
  return nearest;
}

function cross(o, a, b) {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

function closestOnSegment([px, py], [ax, ay], [bx, by]) {
  const dx = bx - ax;
  const dy = by - ay;
  const lengthSq = dx * dx + dy * dy;
  const t = lengthSq ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lengthSq)) : 0;
  return [ax + t * dx, ay + t * dy];
}

function ringArea(ring) {
  let sum = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    sum += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1];
  }
  return Math.abs(sum / 2);
}

// Douglas–Peucker; keeps the first and last point, so a closed ring stays closed.
function simplify(points, tolerance) {
  let maxDistance = 0;
  let index = 0;
  for (let i = 1; i < points.length - 1; i++) {
    const [qx, qy] = closestOnSegment(points[i], points[0], points[points.length - 1]);
    const d = Math.hypot(points[i][0] - qx, points[i][1] - qy);
    if (d > maxDistance) [maxDistance, index] = [d, i];
  }
  if (maxDistance <= tolerance) return [points[0], points[points.length - 1]];
  return [
    ...simplify(points.slice(0, index + 1), tolerance).slice(0, -1),
    ...simplify(points.slice(index), tolerance),
  ];
}

/**
 * Bounding box of a (Multi)Polygon, for fitBounds().
 * @param {GeoJSON.Polygon | GeoJSON.MultiPolygon} geometry
 * @returns {LngLatBounds}
 */
export function geometryBounds(geometry) {
  const bounds = new LngLatBounds();
  const extend = (c) => (typeof c[0] === 'number' ? bounds.extend(c) : c.forEach(extend));
  extend(geometry.coordinates);
  return bounds;
}
