// A "global" variable for all charts
let charts = [];
let lastTimestamp = null; // Track the latest timestamp to fetch only new data

// --- DOM elements (no changes) ---
const flowButton = document.getElementById('flowButton');
const pressureButton = document.getElementById('pressureButton');
const pageHeader = document.getElementById('pageHeader');
const chartsContainer = document.getElementById('chartsContainer');

// A variable to keep track of the current view
let currentView = 'flow'; 

// --- Helper functions (no changes) ---
function activateButton(activeBtn, inactiveBtn) {
    activeBtn.classList.add('active');
    inactiveBtn.classList.remove('active');
}

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// --- Data Fetching (no changes) ---
async function fetchData() {
    try {
        // To optimize, you could pass `lastTimestamp` to the backend
        // e.g., fetch(`.../api/real_sensor_data?since=${lastTimestamp}`)
        const response = await fetch('http://localhost:5000/api/real_sensor_data');
        if (!response.ok) throw new Error('Network response not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

// --- Chart Management ---

function clearCharts() {
    // charts.forEach(chart => chart.destroy());
    charts = [];
    chartsContainer.innerHTML = '';
}

/**
 * Initializes the charts for a specific view (e.g., 'flow' or 'pressure').
 * This function builds the entire chart display from scratch.
 * It should only be called on page load or when switching views.
 */
async function initializeCharts(type) {
    pageHeader.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Sensors`;
    
    // Fetch initial data
    const allData = await fetchData();
    if (!allData || allData.length === 0) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    // This is a full rebuild, so clear everything first
    clearCharts();

    // Store the latest timestamp from the initial data
    lastTimestamp = allData[allData.length - 1].timestamp;

    const sensorKeys = Object.keys(allData[0]).filter(k => k.startsWith(type));

    sensorKeys.forEach((sensorKey, i) => {        
        
        const card = document.createElement('div');
        card.style.marginBottom = '40px';
        card.innerHTML = `
            <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">${sensorKey}</h2>
            <h3 id="latest-data-${i}" style="text-align:center; margin-bottom: 10px;"></h3>
            <canvas id="lineChart${i}"></canvas>
        `;
        chartsContainer.appendChild(card);

        const ctx = document.getElementById(`lineChart${i}`).getContext('2d');
        
        // Show all available points initially
        const initialLabels = allData.map(row => {
            const date = new Date(row.timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });
        const initialActualData = allData.map(row => row[sensorKey]);
        // Assuming AI data is available in a similar structure
        const initialAiData = allData.map(row => row[sensorKey]); // Placeholder for AI data

        // Calculate label display: show all data points, but only show max 10 labels, equally spaced
        const maxLabels = 10;
        const labelCount = initialLabels.length;
        let displayLabels = initialLabels.map((label, idx) => {
            if (labelCount <= maxLabels) return label;
            // Show label if it's at an interval, or the first/last
            const interval = Math.floor((labelCount - 1) / (maxLabels - 1));
            if (idx === 0 || idx === labelCount - 1 || idx % interval === 0) return label;
            return '';
        });

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
            labels: initialLabels,
            datasets: [{
                label: `${sensorKey} (Actual)`,
                data: initialActualData,
                borderColor: 'blue',
                fill: false,
                pointRadius: 0, // Hide dots
                pointHoverRadius: 0 // Hide dots on hover
            }, {
                label: `${sensorKey} (AI Predicted)`,
                data: initialAiData,
                borderColor: 'red',
                fill: false,
                pointRadius: 0, // Hide dots
                pointHoverRadius: 0 // Hide dots on hover
            }]
            },
            options: {
            responsive: true,
            plugins: {
                legend: {
                display: true
                }
            },
            scales: {
                x: {
                ticks: {
                    autoSkip: false,
                    callback: function(value, index) {
                    const allLabels = this.chart.data.labels;
                    const labelCount = allLabels.length;
                    const maxLabels = 10;
                    if (labelCount <= maxLabels) {
                        return allLabels[index];
                    }
                    const interval = Math.floor((labelCount - 1) / (maxLabels - 1));
                    if (index === 0 || index === labelCount - 1) {
                        return allLabels[index];
                    }
                    if (index % interval === 0) {
                        return allLabels[index];
                    }
                    return '';
                    }
                }
                }
            }
            }
        });
        
        // Update the 'Latest Data' heading
        document.getElementById(`latest-data-${i}`).textContent = `Latest Data: ${initialActualData[initialActualData.length - 1] ?? 'N/A'}`;

        charts.push({ chart, sensorKey, latestDataEl: document.getElementById(`latest-data-${i}`) });
    });
}

/**
 * Fetches only the new data and updates the existing charts.
 * This is the function that creates the "sliding" effect.
 */
async function updateChartData() {
    const newData = await fetchData();
    if (!newData || newData.length === 0) return;

    // Find the actual new data points to add
    const newPoints = newData.filter(row => row.timestamp > lastTimestamp);

    if (newPoints.length > 0) {
        // Update the last timestamp with the newest one
        lastTimestamp = newPoints[newPoints.length - 1].timestamp;

        newPoints.forEach(point => {
            charts.forEach(({ chart, sensorKey, latestDataEl }) => {
                // Ensure the chart's datasets exist before trying to push to them
                if (chart.data.labels && chart.data.datasets.length > 0) {
                    const datasets = chart.data.datasets;

                    // Add new data
                    const date = new Date(point.timestamp);
                    const formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    chart.data.labels.push(formattedTime);
                    datasets[0].data.push(point[sensorKey]);
                    datasets[1].data.push(point[sensorKey]); // Placeholder for new AI data point

                    // Remove the oldest data point to create the "slide" effect
                    chart.data.labels.shift();
                    datasets[0].data.shift();
                    datasets[1].data.shift();

                    // Update the "Latest Data" display
                    latestDataEl.textContent = `Latest Data: ${point[sensorKey] ?? 'N/A'}`;
                    
                    // Redraw the chart with a slower animation
                    chart.update();
                }
            });
        });
    }
}


// --- Event Listeners and Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    const initialView = getQueryParam('view') || 'flow';
    currentView = initialView;
    activateButton(initialView === 'flow' ? flowButton : pressureButton, initialView === 'flow' ? pressureButton : flowButton);
    initializeCharts(initialView);
});

flowButton.addEventListener('click', () => {
    if (currentView === 'flow') return; // Don't re-render if view is the same
    currentView = 'flow';
    activateButton(flowButton, pressureButton);
    clearCharts(); // Clear existing charts
    initializeCharts('flow');
});

pressureButton.addEventListener('click', () => {
    if (currentView === 'pressure') return; // Don't re-render if view is the same
    currentView = 'pressure';
    activateButton(pressureButton, flowButton);
    clearCharts(); // Clear existing charts
    initializeCharts('pressure');
});

// Set the interval to check for new data
setInterval(updateChartData, 2000); // Check every 2 seconds