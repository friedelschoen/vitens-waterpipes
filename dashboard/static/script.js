// A "global" variable for all charts
let charts = [];
let lastTimestamp = null; // Track the latest timestamp to fetch only new data

// --- DOM elements (no changes) ---
const pageHeader = document.getElementById('pageHeader');
const chartsContainer = document.getElementById('chartsContainer');
const limit = 100; // Limit for the number of data points to fetch
// A variable to keep track of the current view

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// --- Data Fetching (no changes) ---
async function fetchData() {
    try {
        // To optimize, you could pass `lastTimestamp` to the backend
        // e.g., fetch(`.../api/real_sensor_data?since=${lastTimestamp}`)
        const response = await fetch(`/api/real_sensor_data?limit=${limit}`);
        if (!response.ok) throw new Error('Network response not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

// Fetch simulation data from backend
async function fetchSimulationData() {
    try {
        const response = await fetch(`/api/simulation_data?limit=${limit}`);
        if (!response.ok) throw new Error('Network response not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch simulation error:', error);
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
    // Fetch initial data
    const allData = await fetchData();
    const simulationData = await fetchSimulationData(); // <-- fetch simulated data

    if (!allData || allData.length === 0) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    console.log(allData);
    let sensorKeys = Object.keys(allData.sensors);

    sensorKeys.sort();

    clearCharts();

    lastTimestamp = allData[allData.length - 1].timestamp;

    // Identify the first two sensor keys (should be flow_5 and pressure_6)
    const firstTwoKeys = sensorKeys.slice(0, 2);

    sensorKeys.forEach((sensorKey, i) => {
        const initialActualData = allData.map(row => row[sensorKey]);
        const card = document.createElement('div');
        card.style.marginBottom = '40px';
        card.innerHTML = `
            <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">${sensorKey}</h2>
            <h3 id="latest-data-${i}" style="text-align:center; margin-bottom: 10px;"></h3>
            <canvas id="lineChart${i}"></canvas>
        `;
        chartsContainer.appendChild(card);

        const ctx = document.getElementById(`lineChart${i}`).getContext('2d');
        const initialLabels = allData.map(row => {
            const date = new Date(row.timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });

        let datasets = [
            {
                label: `${sensorKey} (Actual)`,
                data: initialActualData,
                borderColor: 'blue',
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 0
            }
        ];

        // Only add simulated data for flow_5 and pressure_6 (the first two graphs)
        if (simulationData && firstTwoKeys.includes(sensorKey)) {
            const simData = simulationData.map(row => row[sensorKey]);
            datasets.push({
                label: `${sensorKey} (Simulated)`,
                data: simData,
                borderColor: 'red',
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 0
            });
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
            labels: initialLabels,
            datasets: datasets
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
                },
                y: {
                min: type === 'flow' ? 0 : 0,
                max: type === 'flow' ? 30 : 1
                }
            }
            }
        });

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
    const simulationData = await fetchSimulationData(); // Fetch new simulation data as well
    if (!newData || newData.length === 0) return;

    // Find the actual new data points to add
    const newPoints = newData.filter(row => row.timestamp > lastTimestamp);

    if (newPoints.length > 0) {
        lastTimestamp = newPoints[newPoints.length - 1].timestamp;

        charts.forEach(({ chart, sensorKey, latestDataEl }, i) => {
            // Add new labels and data
            newPoints.forEach((row, idx) => {
                const date = new Date(row.timestamp);
                const label = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                chart.data.labels.push(label);

                // Always update actual data
                chart.data.datasets[0].data.push(row[sensorKey]);

                // Only update simulated data for flow_5 and pressure_6 (the first two charts)
                if (
                    chart.data.datasets.length > 1 &&
                    (sensorKey === 'flow_5' || sensorKey === 'pressure_6') &&
                    simulationData && simulationData.length > idx
                ) {
                    chart.data.datasets[1].data.push(simulationData[idx][sensorKey]);
                }
            });

            // Keep data arrays within the limit
            while (chart.data.labels.length > 100) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
                if (
                    chart.data.datasets.length > 1 &&
                    (sensorKey === 'flow_5' || sensorKey === 'pressure_6')
                ) {
                    chart.data.datasets[1].data.shift();
                }
            }

            // Update latest value text
            latestDataEl.textContent = `Latest Data: ${chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1] ?? 'N/A'}`;

            chart.update();
        });
    }
}

// --- Event Listeners and Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    const initialView = getQueryParam('view') || 'flow';
    initializeCharts(initialView);
});


// Set the interval to check for new data
setInterval(updateChartData, 2000); // Check every 2 seconds

function renderValvesView() {
    const main = document.getElementById('mainContent');
    main.innerHTML = `
        <section id="valves" class="py-12 px-6 sm:px-12">
            <div class="flex flex-wrap justify-center gap-8">
                <!-- Repeat for each valve, or generate dynamically -->
                <div class="bg-white rounded-xl mt-4 p-6 w-72 shadow-md flex flex-col items-center">
                    <h2 class="text-xl font-semibold mb-2 text-gray-800">Valve 1</h2>
                    <p class="mb-4 text-gray-500">
                        Valve 1 is now <span id="valve-state-1" class="font-semibold text-red-400">closed</span>
                    </p>
                    <div class="flex gap-4">
                        <button class="bg-neutral-700 hover:bg-neutral-800 text-white font-medium py-2 px-5 rounded transition"
                            data-valve="1" data-action="open" id="open-btn-1">Open</button>
                        <button class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-5 rounded transition"
                            data-valve="1" data-action="close" id="close-btn-1">Close</button>
                    </div>
                </div>
                <!-- ...repeat for valves 2-6... -->
            </div>
        </section>
    `;
    // Now call your setupValveListeners() and fetchValveStates()
    fetchValveStates();
    setupValveListeners();
}

// In your DOMContentLoaded or router logic:
document.addEventListener('DOMContentLoaded', () => {
    const view = getQueryParam('view') || 'flow';
    if (view === 'valves') {
        renderValvesView();
    } else {
        // ...existing chart logic...
    }
});