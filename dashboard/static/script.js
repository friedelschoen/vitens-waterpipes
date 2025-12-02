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
        const response = await fetch(`/api/sensor_data?limit=${limit}`);
        if (!response.ok) throw new Error('Network response not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

// --- Data Fetching (no changes) ---
async function getValves() {
    try {
        const response = await fetch(`/api/get_valves`);
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
    // Fetch initial data
    const allData = await fetchData();

    if (!allData || allData.length === 0) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    let sensorKeys = Object.keys(allData[0].sensors);

    sensorKeys.sort();

    clearCharts();

    lastTimestamp = allData[allData.length - 1].timestamp;

    // // Identify the first two sensor keys (should be flow_5 and pressure_6)
    // const firstTwoKeys = sensorKeys.slice(0, 2);

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

        // // Only add simulated data for flow_5 and pressure_6 (the first two graphs)
        // if (simulationData && firstTwoKeys.includes(sensorKey)) {
        //     const simData = simulationData.map(row => row[sensorKey]);
        //     datasets.push({
        //         label: `${sensorKey} (Simulated)`,
        //         data: simData,
        //         borderColor: 'red',
        //         fill: false,
        //         pointRadius: 0,
        //         pointHoverRadius: 0
        //     });
        // }

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
    // const simulationData = await fetchSimulationData(); // Fetch new simulation data as well
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
                chart.data.datasets[0].data.push(row.sensors[sensorKey].value);
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

async function createValves() {
    let valves = await getValves();
    console.log(valves);
    let valvesDiv = document.getElementById("valves-div");
    for (let name in valves) {
        valvesDiv.innerHTML += `
        <!-- Valve ${name} -->
        <div class="bg-white rounded-xl mt-4 p-6 w-72 shadow-md flex flex-col items-center">
            <h2 class="text-xl font-semibold mb-2 text-gray-800">Valve ${name}</h2>
            <p class="mb-4 text-gray-500">
                Valve ${name} is now <span id="valve-state-${name}" class="font-semibold text-red-400">closed</span>
            </p>
            <div class="flex gap-4">
                <button
                    class="bg-neutral-700 hover:bg-neutral-800 text-white font-medium py-2 px-5 rounded transition"
                    data-valve="${name}" data-action="open" id="open-btn-${name}">
                    Open
                </button>
                <button
                    class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-5 rounded transition"
                    data-valve="${name}" data-action="close" id="close-btn-${name}">
                    Close
                </button>
            </div>
        </div>
        `;

        updateValveText(name, valves[name]);

    setTimeout(() => {
        const initialView = getQueryParam('view') || 'flow';
        initializeCharts(initialView);

        const openBtn = document.getElementById(`open-btn-${name}`);
        const closeBtn = document.getElementById(`close-btn-${name}`);
        openBtn.addEventListener('click', handleValveButtonClick);
        closeBtn.addEventListener('click', handleValveButtonClick);
    }, 500);

    }
}
createValves()

function updateValveText(valve, state) {
    const stateSpan = document.getElementById(`valve-state-${valve}`);
    const openBtn = document.getElementById(`open-btn-${valve}`);
    const closeBtn = document.getElementById(`close-btn-${valve}`);

    // Update state text and color
    if (stateSpan) {
        stateSpan.classList.remove('text-green-500', 'text-red-400', 'text-black', 'font-bold', 'font-semibold');
        if (state === 1) {
            stateSpan.textContent = 'open';
            stateSpan.classList.add('text-green-500', 'font-bold');
        } else {
            stateSpan.textContent = 'closed';
            stateSpan.classList.add('text-red-400', 'font-bold');
        }
    }

    // Update button styles
    if (openBtn && closeBtn) {
        openBtn.disabled = false;
        closeBtn.disabled = false;
        openBtn.classList.remove(
            'bg-green-500', 'text-white', 'font-bold', 'ring', 'ring-green-300',
            'bg-neutral-700', 'hover:bg-neutral-800',
            'bg-gray-300', 'hover:bg-gray-400', 'text-gray-800'
        );
        closeBtn.classList.remove(
            'bg-red-500', 'text-white', 'font-bold', 'ring', 'ring-red-300',
            'bg-gray-300', 'hover:bg-gray-400', 'text-gray-800',
            'bg-neutral-700', 'hover:bg-neutral-800'
        );

        if (state === 1) {
            openBtn.classList.add('bg-green-500', 'text-white', 'font-bold', 'ring', 'ring-green-300');
            closeBtn.classList.add('bg-gray-300', 'hover:bg-gray-400', 'text-gray-800');
        } else {
            closeBtn.classList.add('bg-red-500', 'text-white', 'font-bold', 'ring', 'ring-red-300');
            openBtn.classList.add('bg-gray-300', 'hover:bg-gray-400', 'text-gray-800');
        }
    }
}

function handleValveButtonClick(e) {
    // console.log(valve);

    const valve = e.target.getAttribute('data-valve');
    const action = e.target.getAttribute('data-action');
    // if (!valve) return;
    updateValveText(valve, action);
    console.log(valve);
    fetch('http://localhost:5000/api/set_valve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ valve: valve, state: action })
    });
}
