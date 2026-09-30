/**
 * main.js
 * =======
 * AquaGuard AI Client Application Logic
 * Integrates Leaflet GIS, Chart.js, real-time risk scenario simulation,
 * intervention impact calculations, explainability diagnostics, and report exports.
 */

let map = null;
let geoJsonLayers = {};
let allWatersheds = [];
let activeWatershed = null;
let activeScoreData = null;
let contributionChart = null;

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  setupEventListeners();
  loadWatersheds();
});

/**
 * 1. Initialize Leaflet Map focused on India extent
 */
function initMap() {
  // Center roughly over central India
  map = L.map('map', {
    zoomControl: true,
    attributionControl: false
  }).setView([21.5, 78.9], 5);

  // Free OpenStreetMap Tiles (Works completely without external API keys or tokens)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    minZoom: 4
  }).addTo(map);

  // Attribution watermark
  L.control.attribution({ position: 'bottomright' })
    .addAttribution('&copy; OpenStreetMap contributors | AquaGuard AI')
    .addTo(map);
}

/**
 * 2. Setup All Interactive UI Listeners
 */
function setupEventListeners() {
  // Search bar filtering
  document.getElementById('ws-search-input').addEventListener('input', (e) => {
    filterWatershedList(e.target.value);
  });

  // Map Reset Extent Button
  document.getElementById('btn-reset-map').addEventListener('click', () => {
    map.flyTo([21.5, 78.9], 5, { duration: 1.2 });
  });

  // Explain Score Button & Modal Close
  document.getElementById('btn-explain-score').addEventListener('click', () => {
    openExplainModal();
  });
  document.getElementById('btn-formula-modal').addEventListener('click', () => {
    openExplainModal();
  });
  document.getElementById('btn-close-explain-modal').addEventListener('click', () => {
    document.getElementById('explain-score-modal').classList.remove('active');
  });

  // Modal download PDF shortcut
  document.getElementById('btn-modal-download-pdf').addEventListener('click', () => {
    downloadActivePdf();
  });

  // Global Download PDF button
  document.getElementById('btn-download-pdf').addEventListener('click', () => {
    downloadActivePdf();
  });

  // Water Risk Climate Simulator Controls
  const rainSlider = document.getElementById('slider-rainfall-drop');
  const rainValLabel = document.getElementById('val-rainfall-drop');
  rainSlider.addEventListener('input', (e) => {
    rainValLabel.textContent = `${e.target.value > 0 ? '+' : ''}${e.target.value}%`;
  });

  const ndviSlider = document.getElementById('slider-ndvi-drop');
  const ndviValLabel = document.getElementById('val-ndvi-drop');
  ndviSlider.addEventListener('input', (e) => {
    ndviValLabel.textContent = `${e.target.value > 0 ? '+' : ''}${e.target.value}%`;
  });

  // Run Risk Scenario
  document.getElementById('btn-apply-risk-sim').addEventListener('click', () => {
    runRiskSimulation();
  });

  // Reset Risk Simulator
  document.getElementById('btn-reset-risk-sim').addEventListener('click', () => {
    rainSlider.value = 0;
    ndviSlider.value = 0;
    rainValLabel.textContent = '0%';
    ndviValLabel.textContent = '0%';
    loadWatersheds(); // re-fetch baseline
  });

  // Intervention Checkboxes
  const checklist = document.getElementById('intervention-checklist');
  checklist.querySelectorAll('.intervention-checkbox-item').forEach(item => {
    item.addEventListener('click', (e) => {
      // Toggle checkbox
      const checkbox = item.querySelector('input[type="checkbox"]');
      if (e.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
      }
      if (checkbox.checked) {
        item.classList.add('checked');
      } else {
        item.classList.remove('checked');
      }
      runInterventionSimulation();
    });
  });

  // Reset Interventions Button
  document.getElementById('btn-reset-interventions').addEventListener('click', () => {
    checklist.querySelectorAll('.intervention-checkbox-item').forEach(item => {
      item.classList.remove('checked');
      item.querySelector('input[type="checkbox"]').checked = false;
    });
    runInterventionSimulation();
  });
}

/**
 * 3. Fetch all watersheds from backend and render map + list
 */
function loadWatersheds() {
  fetch('/api/watersheds')
    .then(res => res.json())
    .then(data => {
      allWatersheds = data.watersheds;
      renderRankedList(allWatersheds);
      renderMapPolygons(allWatersheds);
      updateAggregateStats(allWatersheds);

      // Select first critical watershed by default
      if (allWatersheds.length > 0) {
        selectWatershed(allWatersheds[0].id);
      }
    })
    .catch(err => console.error("Error loading watersheds:", err));
}

/**
 * 4. Render National Priority Counts
 */
function updateAggregateStats(watersheds) {
  let crit = 0, high = 0, med = 0, low = 0;
  watersheds.forEach(w => {
    const s = w.score_data.composite_score;
    if (s >= 7.5) crit++;
    else if (s >= 5.5) high++;
    else if (s >= 4.0) med++;
    else low++;
  });
  document.getElementById('count-critical').textContent = crit;
  document.getElementById('count-high').textContent = high;
  document.getElementById('count-medium').textContent = med;
  document.getElementById('count-low').textContent = low;
  document.getElementById('total-count-badge').textContent = `${watersheds.length} Basins`;
}

/**
 * 5. Render Ranked Watershed List in Sidebar
 */
function renderRankedList(watersheds) {
  const container = document.getElementById('watershed-list-container');
  container.innerHTML = '';

  watersheds.forEach((w, index) => {
    const item = document.createElement('div');
    item.className = `watershed-item ${activeWatershed && activeWatershed.id === w.id ? 'active' : ''}`;
    item.id = `ws-item-${w.id}`;

    const score = w.score_data ? w.score_data.composite_score : w.score;
    const badgeColor = w.score_data ? w.score_data.badge_color : (w.badge_color || '#ef4444');
    const priority = w.score_data ? w.score_data.priority : w.priority;

    item.innerHTML = `
      <div class="ws-item-header">
        <span class="ws-rank">#${index + 1} Priority</span>
        <span class="ws-score-badge" style="background: ${badgeColor}22; color: ${badgeColor}; border: 1px solid ${badgeColor}55;">
          <i class="fa-solid fa-droplet" style="font-size: 0.75rem;"></i> ${score}
        </span>
      </div>
      <div class="ws-name">${w.name}</div>
      <div class="ws-loc"><i class="fa-solid fa-location-dot" style="font-size: 0.7rem; color: var(--accent-cyan);"></i> ${w.district}, ${w.state}</div>
      <div class="ws-meta-row">
        <span>Rain: ${w.rainfall_mm}mm</span>
        <span>Slope: ${w.slope_deg}°</span>
        <span style="color: ${badgeColor}; font-weight: 600;">${priority.split(' ')[0]}</span>
      </div>
    `;

    item.addEventListener('click', () => {
      selectWatershed(w.id);
    });

    container.appendChild(item);
  });
}

/**
 * 6. Render GeoJSON/Polygons on Leaflet Map
 */
function renderMapPolygons(watersheds) {
  // Clear existing layers
  Object.values(geoJsonLayers).forEach(layer => map.removeLayer(layer));
  geoJsonLayers = {};

  watersheds.forEach(w => {
    const score = w.score_data ? w.score_data.composite_score : w.score;
    const color = w.score_data ? w.score_data.badge_color : (w.badge_color || '#ef4444');

    const polygon = L.polygon(w.polygon, {
      color: color,
      fillColor: color,
      fillOpacity: 0.45,
      weight: 2
    }).addTo(map);

    // Popup content with real actions
    const popupContent = `
      <div style="font-family: 'Inter', sans-serif; min-width: 220px; color: #0f172a;">
        <div style="font-weight: 800; font-size: 1rem; color: #0284c7; margin-bottom: 2px;">${w.name}</div>
        <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 8px;">${w.district}, ${w.state} (${w.id})</div>
        <div style="display: flex; justify-content: space-between; background: #f1f5f9; padding: 6px 8px; border-radius: 6px; margin-bottom: 8px;">
          <span style="font-size: 0.8rem; font-weight: 600;">Stress Score:</span>
          <span style="font-size: 0.85rem; font-weight: 800; color: ${color};">${score} / 10.0</span>
        </div>
        <div style="font-size: 0.72rem; color: #475569; line-height: 1.4; margin-bottom: 10px;">
          • Rainfall: <b>${w.rainfall_mm} mm</b><br>
          • Dominant Soil: <b>${w.soil_type}</b><br>
          • Drainage: <b>${w.drainage_density_km_per_sq_km} km/km²</b>
        </div>
        <button onclick="window.selectWatershedFromMap('${w.id}')" style="width: 100%; background: #0284c7; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 0.78rem; cursor: pointer;">
          Select & Analyze Interventions
        </button>
      </div>
    `;

    polygon.bindPopup(popupContent);
    polygon.on('click', () => {
      selectWatershed(w.id);
    });

    geoJsonLayers[w.id] = polygon;
  });
}

// Global hook for popup button
window.selectWatershedFromMap = function(wid) {
  selectWatershed(wid);
};

/**
 * 7. Select a Watershed and Update All Dashboard Elements
 */
function selectWatershed(wid) {
  fetch(`/api/watershed/${wid}`)
    .then(res => res.json())
    .then(data => {
      activeWatershed = data.watershed;
      activeScoreData = data.score_data;

      // Update sidebar highlight
      document.querySelectorAll('.watershed-item').forEach(el => el.classList.remove('active'));
      const activeEl = document.getElementById(`ws-item-${wid}`);
      if (activeEl) {
        activeEl.classList.add('active');
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      // Fly map to polygon center
      if (activeWatershed.coordinates && map) {
        map.flyTo(activeWatershed.coordinates, 9, { duration: 1.0 });
        if (geoJsonLayers[wid]) {
          geoJsonLayers[wid].openPopup();
        }
      }

      // Update Active Watershed Diagnostic Card
      document.getElementById('detail-ws-name').textContent = activeWatershed.name;
      document.getElementById('detail-ws-loc').textContent = `${activeWatershed.district}, ${activeWatershed.state} (Area: ${activeWatershed.area_sq_km} sq km | Pop: ${activeWatershed.population.toLocaleString()})`;
      document.getElementById('detail-score-val').textContent = `${activeScoreData.composite_score} / 10`;
      document.getElementById('detail-score-val').style.color = activeScoreData.badge_color;

      // Update Parameter Specs
      document.getElementById('spec-rainfall').textContent = `${activeWatershed.rainfall_mm} mm`;
      document.getElementById('spec-ndvi').textContent = activeWatershed.ndvi;
      document.getElementById('spec-slope').textContent = `${activeWatershed.slope_deg}°`;
      document.getElementById('spec-dd').textContent = `${activeWatershed.drainage_density_km_per_sq_km} km/km²`;
      document.getElementById('spec-soil').textContent = activeWatershed.soil_type;
      document.getElementById('spec-sw').textContent = `${activeWatershed.surface_water_pct}%`;

      // Trigger automatic intervention simulation
      runInterventionSimulation();
    })
    .catch(err => console.error("Error selecting watershed:", err));
}

/**
 * 8. Run Intervention Impact Simulator
 */
function runInterventionSimulation() {
  if (!activeWatershed) return;

  const checklist = document.getElementById('intervention-checklist');
  const selected = [];
  checklist.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
    selected.push(cb.value);
  });

  const rainDrop = parseFloat(document.getElementById('slider-rainfall-drop').value) || 0;

  fetch('/api/simulate-interventions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      watershed_id: activeWatershed.id,
      interventions: selected,
      rainfall_drop_pct: rainDrop < 0 ? Math.abs(rainDrop) : 0
    })
  })
    .then(res => res.json())
    .then(data => {
      const sim = data.simulation;
      document.getElementById('sim-res-curr').textContent = sim.current_score;
      document.getElementById('sim-res-pred').textContent = sim.predicted_score;
      document.getElementById('sim-res-pred').style.color = sim.pred_color;
      document.getElementById('sim-res-redux').textContent = `-${sim.risk_reduction_pct}%`;
      document.getElementById('sim-res-recharge').textContent = `+${sim.estimated_recharge_gain_mcm} MCM`;
      document.getElementById('sim-res-combo').textContent = sim.recommended_combo;
    })
    .catch(err => console.error("Error running intervention simulation:", err));
}

/**
 * 9. Run Water Risk Scenario (Climate Stress Test)
 */
function runRiskSimulation() {
  const rainDrop = parseFloat(document.getElementById('slider-rainfall-drop').value) || 0;
  const ndviDrop = parseFloat(document.getElementById('slider-ndvi-drop').value) || 0;

  fetch('/api/simulate-risk-scenario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rainfall_change_pct: rainDrop,
      ndvi_change_pct: ndviDrop
    })
  })
    .then(res => res.json())
    .then(data => {
      allWatersheds = data.watersheds;
      renderRankedList(allWatersheds);
      renderMapPolygons(allWatersheds);
      updateAggregateStats(allWatersheds);

      // Keep active watershed updated
      if (activeWatershed) {
        selectWatershed(activeWatershed.id);
      }
    })
    .catch(err => console.error("Error in risk simulation:", err));
}

/**
 * 10. Open Explain Score Modal with Chart.js Breakdown
 */
function openExplainModal() {
  if (!activeWatershed || !activeScoreData) return;

  const modal = document.getElementById('explain-score-modal');
  modal.classList.add('active');

  document.getElementById('explain-ws-name').textContent = `${activeWatershed.name} (${activeWatershed.id})`;
  document.getElementById('modal-formula-display').textContent = activeScoreData.formula_text;

  // Populate Table
  const tbody = document.getElementById('explain-table-body');
  tbody.innerHTML = '';

  const contrib = activeScoreData.contributions_pct;
  const norm = activeScoreData.normalized;
  const weights = activeScoreData.weights;

  const paramLabels = [
    { key: 'rainfall', label: 'Rainfall Deficit' },
    { key: 'ndvi', label: 'Vegetation / NDVI' },
    { key: 'slope', label: 'Slope / Relief' },
    { key: 'soil', label: 'Soil Vulnerability' },
    { key: 'drainage_density', label: 'Drainage Density' },
    { key: 'surface_water', label: 'Surface Storage Deficit' },
    { key: 'land_use', label: 'Land Use Vulnerability' }
  ];

  const chartLabels = [];
  const chartValues = [];
  const chartColors = [
    '#38bdf8', '#10b981', '#f59e0b', '#f97316', '#a855f7', '#06b6d4', '#ec4899'
  ];

  paramLabels.forEach((p, idx) => {
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid rgba(255, 255, 255, 0.05)';
    tr.innerHTML = `
      <td style="padding: 6px; color: #fff;">${p.label}</td>
      <td style="padding: 6px; color: var(--text-dim);">${Math.round(weights[p.key] * 100)}%</td>
      <td style="padding: 6px; color: var(--accent-cyan); font-weight: 600;">${norm[p.key]}</td>
      <td style="padding: 6px; color: #fff; font-weight: 700;">${contrib[p.key]}%</td>
    `;
    tbody.appendChild(tr);

    chartLabels.push(p.label);
    chartValues.push(contrib[p.key]);
  });

  // Render or Update Doughnut Chart
  renderContributionChart(chartLabels, chartValues, chartColors);
}

/**
 * 11. Render Doughnut Chart for Score Contributions
 */
function renderContributionChart(labels, values, colors) {
  const ctx = document.getElementById('contributionChart').getContext('2d');
  if (contributionChart) {
    contributionChart.destroy();
  }

  contributionChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 1,
        borderColor: '#0f172a'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.label}: ${context.raw}% contribution`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

/**
 * 12. Filter list by text search
 */
function filterWatershedList(query) {
  const term = query.toLowerCase().trim();
  const filtered = allWatersheds.filter(w => 
    w.name.toLowerCase().includes(term) ||
    w.district.toLowerCase().includes(term) ||
    w.state.toLowerCase().includes(term) ||
    w.id.toLowerCase().includes(term)
  );
  renderRankedList(filtered);
}

/**
 * 13. Download Diagnostic PDF for active watershed
 */
function downloadActivePdf() {
  if (!activeWatershed) return;

  const checklist = document.getElementById('intervention-checklist');
  const selected = [];
  checklist.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
    selected.push(cb.value);
  });

  const rainDrop = parseFloat(document.getElementById('slider-rainfall-drop').value) || 0;
  const url = `/api/export/pdf?id=${activeWatershed.id}&interventions=${encodeURIComponent(selected.join(','))}&rainfall_drop_pct=${Math.abs(rainDrop)}`;

  window.location.href = url;
}
