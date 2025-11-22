// static/scripts/map.js
const AEWMap = (function () {
  const map = L.map('map').setView([12, -20], 4);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    subdomains: 'abcd',
    maxZoom: 20
  }).addTo(map);

  const trackLayer = L.layerGroup().addTo(map);
  let currentHighlighted = null;

  function getColor(strength_x1e5) {
    if (strength_x1e5 <= 1.5) return '#1c54ff';
    if (strength_x1e5 <= 3.0) return '#6cc343';
    if (strength_x1e5 <= 4.2) return '#ffc309';
    if (strength_x1e5 <= 5.0) return '#ff7209';
    if (strength_x1e5 <= 5.8) return '#e83b0c';
    if (strength_x1e5 <= 6.5) return '#e80cae';
    return '#bd00ff';
  }

  function clearMap() {
    trackLayer.clearLayers();
    currentHighlighted = null;
  }

  function applyTooltipStyle(tooltip, color) {
    if (!tooltip?._container) return;
    const el = tooltip._container;
    el.style.border = `3px solid ${color}`;
    el.style.backgroundColor = 'rgba(15, 20, 40, 0.96)';
    el.style.boxShadow = `0 3px 14px ${color}88, 0 0 0 1px ${color}44`;
    el.style.backdropFilter = 'blur(8px)';
  }

  function renderTracks(features, monthFilter, pointsOnly, onPointClick) {
    clearMap();
    if (!features || features.length === 0) return;

    const visible = monthFilter === 'all'
      ? features
      : features.filter(f => f.properties.months.includes(parseInt(monthFilter)));

    visible.forEach(feature => {
      const coords = feature.geometry.coordinates;
      const points = feature.properties.point_data;
      const layers = [];

      if (pointsOnly) {
        // ——— POINTS ONLY MODE ———
        points.forEach((pt, i) => {
          const s = pt.strength * 1e5;
          const color = getColor(s);

          const circle = L.circleMarker([coords[i][1], coords[i][0]], {
            radius: 7,
            fillColor: color,
            fillOpacity: 0.98,
            color: 'transparent',
            weight: 0
          });

          circle.on('click', () => onPointClick(pt.time.split(' ')[0], s.toFixed(2)));

          const tooltipContent = `<strong>Date:</strong> ${pt.time.split(' ')[0]}<br><strong>Vorticity:</strong> ${s.toFixed(2)} ×10⁻⁵ s⁻¹`;

          circle.bindTooltip(tooltipContent, {
            sticky: true,
            className: 'aew-vorticity-tooltip',
            animation: false   // ← Instant appearance, no zoom/fly-in
          });

          circle.on('tooltipopen', e => applyTooltipStyle(e.tooltip, color));

          layers.push(circle);
        });
      } else {
        // ——— LINES MODE ———
        for (let i = 0; i < coords.length - 1; i++) {
          const s = points[i].strength * 1e5;
          const color = getColor(s);

          const line = L.polyline(
            [[coords[i][1], coords[i][0]], [coords[i+1][1], coords[i+1][0]]],
            { color: color, weight: 4, opacity: 0.92 }
          );

          line.on('click', () => onPointClick(points[i].time.split(' ')[0], s.toFixed(2)));

          const tooltipContent = `<strong>Date:</strong> ${points[i].time.split(' ')[0]}<br><strong>Vorticity:</strong> ${s.toFixed(2)} ×10⁻⁵ s⁻¹`;

          line.bindTooltip(tooltipContent, {
            sticky: true,
            className: 'aew-vorticity-tooltip',
            animation: false   // ← Instant appearance, no zoom/fly-in
          });

          line.on('tooltipopen', e => applyTooltipStyle(e.tooltip, color));

          layers.push(line);
        }
      }

      const group = L.featureGroup(layers).addTo(trackLayer);

      // Track highlighting on click
      group.on('click', e => {
        L.DomEvent.stopPropagation(e);
        if (currentHighlighted === group) return;

        // Reset previous highlight
        if (currentHighlighted) {
          currentHighlighted.eachLayer(l => l.setStyle?.({
            opacity: pointsOnly ? 0.98 : 0.92,
            fillOpacity: 0.98,
            weight: pointsOnly ? 0 : 4,
            radius: pointsOnly ? 7 : undefined
          }));
        }

        // Dim all other tracks
        trackLayer.eachLayer(g => {
          if (g !== group) {
            g.eachLayer(l => l.setStyle?.({
              opacity: 0.25,
              fillOpacity: 0.25,
              weight: pointsOnly ? 0 : 1.5
            }));
          }
        });

        // Highlight selected track
        group.eachLayer(l => l.setStyle?.({
          weight: pointsOnly ? 0 : 10,
          opacity: 1,
          fillOpacity: 1,
          radius: pointsOnly ? 11 : undefined
        }));

        currentHighlighted = group;
      });
    });

    // Auto-zoom to fit all visible tracks
    if (trackLayer.getLayers().length > 0) {
      try { map.fitBounds(trackLayer.getBounds().pad(0.3)); }
      catch(e) { console.warn("fitBounds skipped"); }
    }
  }

  function resetHighlight() {
    if (!currentHighlighted) return;
    const pointsOnly = document.getElementById('showPointsOnly')?.checked ?? false;

    trackLayer.eachLayer(g => {
      g.eachLayer(l => l.setStyle?.({
        opacity: pointsOnly ? 0.98 : 0.92,
        fillOpacity: 0.98,
        weight: pointsOnly ? 0 : 4,
        radius: pointsOnly ? 7 : undefined
      }));
    });
    currentHighlighted = null;
  }

  map.on('dblclick', resetHighlight);

  return {
    renderTracks,
    clearMap,
    resetHighlight
  };
})();