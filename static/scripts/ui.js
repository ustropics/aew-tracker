// static/scripts/ui.js
document.addEventListener('DOMContentLoaded', () => {
  const waitForMap = setInterval(() => {
    if (typeof AEWMap !== 'undefined') {
      clearInterval(waitForMap);
      startApp();
    }
  }, 50);

  function startApp() {
    let allFeatures = [];
    let currentYear = '2023';
    let dataLoaded = false;

    const trackCountEl      = document.getElementById('trackCount');
    const selectedInfo      = document.getElementById('selectedInfo');
    const selectedDateEl    = document.getElementById('selectedDate');
    const selectedValueEl   = document.getElementById('selectedValue');
    const yearFilter        = document.getElementById('yearFilter');
    const monthFilter       = document.getElementById('monthFilter');
    const showPointsOnly    = document.getElementById('showPointsOnly');

    // UPDATED: now accepts optional feature properties
    const showInfo = (date, value, featureProps = null) => {
      selectedDateEl.textContent = `Date: ${date}`;
      selectedValueEl.textContent = `Vorticity: ${value} ×10⁻⁵ s⁻¹`;

      // Remove any previous TC info
      const existing = selectedInfo.querySelector('.tc-extra-info');
      if (existing) existing.remove();

      // If this is a TC precursor → add rich info
      if (featureProps?.developed_into_tc && featureProps.tc_name) {
        const div = document.createElement('div');
        div.className = 'tc-extra-info';
        div.style.marginTop = '12px';
        div.style.paddingTop = '10px';
        div.style.borderTop = '1px solid rgba(255,255,255,0.25)';
        div.style.fontSize = '14.5px';
        div.innerHTML = `
          <div style="color:#ff6b6b; font-weight:bold; font-size:1.35em; margin-bottom:4px;">
            ${featureProps.tc_name}
          </div>
          <div style="color:#ccc;">
            Developed into Tropical Cyclone<br>
            Genesis: ${featureProps.tc_genesis_time ? featureProps.tc_genesis_time.split(' ')[0] : '—'}
          </div>
        `;
        selectedInfo.appendChild(div);
      }

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

    const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];

    const redrawMap = () => {
      if (!dataLoaded) return;

      const month = monthFilter.value;
      const monthName = month === "all" ? "All Months" : monthNames[parseInt(month) - 1];
      const pointsOnly = showPointsOnly.checked;

      // UPDATED: pass full callback with properties
      AEWMap.renderTracks(allFeatures, month, pointsOnly, (date, value, props) => {
        showInfo(date, value, props);
      });

      const visible = month === 'all'
        ? allFeatures.length
        : allFeatures.filter(f => f.properties.months.includes(parseInt(month))).length;

      trackCountEl.textContent = `${visible} tracks shown (${monthName} ${currentYear})`;
    };

    // Event Listeners
    yearFilter.addEventListener('change', e => loadDataForYear(e.target.value));
    monthFilter.addEventListener('change', redrawMap);
    showPointsOnly.addEventListener('change', redrawMap);

    document.getElementById('map').addEventListener('dblclick', () => {
      hideInfo();
      AEWMap.resetHighlight();
    });

    // Initial load
    loadDataForYear('2023');
  }
});