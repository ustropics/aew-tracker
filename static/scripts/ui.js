// static/scripts/ui.js
document.addEventListener('DOMContentLoaded', () => {
  // Wait until AEWMap (from map.js) is defined
  const waitForMap = setInterval(() => {
    if (typeof AEWMap !== 'undefined') {
      clearInterval(waitForMap);
      startApp();
    }
  }, 50);

  function startApp() {
    let allFeatures = [];
    let currentYear = '1995';
    let dataLoaded = false;

    // These elements are guaranteed to exist now
    const trackCountEl      = document.getElementById('trackCount');
    const selectedInfo      = document.getElementById('selectedInfo');
    const selectedDateEl    = document.getElementById('selectedDate');
    const selectedValueEl   = document.getElementById('selectedValue');
    const yearFilter        = document.getElementById('yearFilter');
    const monthFilter       = document.getElementById('monthFilter');
    const showPointsOnly    = document.getElementById('showPointsOnly');

    const showInfo = (date, value) => {
      selectedDateEl.textContent = `Date: ${date}`;
      selectedValueEl.textContent = `Vorticity: ${value} ×10⁻⁵ s⁻¹`;
      selectedInfo.classList.add('visible');
    };

    const hideInfo = () => selectedInfo.classList.remove('visible');

    const loadDataForYear = (year) => {
      const url = `static/json/aew_tracks_${year}_interactive.json`;
      trackCountEl.textContent = `Loading ${year}...`;
      hideInfo();
      AEWMap.clearMap();

      fetch(url)
        .then(r => {
          if (!r.ok) throw new Error(r.status === 404 ? `Year ${year} not found` : `HTTP ${r.status}`);
          return r.json();
        })
        .then(data => {
          allFeatures = data.features || [];
          dataLoaded = true;
          currentYear = year;
          trackCountEl.textContent = `${allFeatures.length} tracks loaded (${year})`;
          redrawMap();
        })
        .catch(err => {
          console.error(err);
          trackCountEl.textContent = `Error: ${err.message}`;
          allFeatures = [];
          dataLoaded = false;
        });
    };

    const redrawMap = () => {
      if (!dataLoaded) return;

      const month = monthFilter.value;
      const pointsOnly = showPointsOnly.checked;

      AEWMap.renderTracks(allFeatures, month, pointsOnly, showInfo);

      const visible = month === 'all'
        ? allFeatures.length
        : allFeatures.filter(f => f.properties.months.includes(parseInt(month))).length;

      trackCountEl.textContent = `${visible} tracks shown (${currentYear})`;
    };

    // ------------------- Event Listeners -------------------
    yearFilter.addEventListener('change', e => loadDataForYear(e.target.value));
    monthFilter.addEventListener('change', redrawMap);
    showPointsOnly.addEventListener('change', redrawMap);

    document.getElementById('map').addEventListener('dblclick', () => {
      hideInfo();
      AEWMap.resetHighlight();
    });

    // Initial load
    loadDataForYear('1995');
  }
});