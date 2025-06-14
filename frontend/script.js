let charts = [];
let allData = null;
let lastTimestamp = null; // Track the latest timestamp

const flowButton = document.getElementById('flowButton');
const pressureButton = document.getElementById('pressureButton');
const pageHeader = document.getElementById('pageHeader');
const chartsContainer = document.getElementById('chartsContainer');

function activateButton(activeBtn, inactiveBtn) {
    activeBtn.classList.add('active');
    inactiveBtn.classList.remove('active');
}

// Functie om query params te lezen
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

async function fetchData() {
    try {
        const response = await fetch('http://localhost:5000/api/real_sensor_data');
        if (!response.ok) throw new Error('Network response not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

function clearCharts() {
    charts.forEach(chart => chart.destroy());
    charts = [];
    chartsContainer.innerHTML = '';
}

function transformBackendData(rawData, type) {
    // type: 'flow' or 'pressure'
    // Get sensor keys
    const sensorKeys = Object.keys(rawData[0]).filter(k => k.startsWith(type));
    // Build datasets for each sensor
    return sensorKeys.map(sensorKey => {
        return {
            type: 'line',
            data: {
                labels: rawData.map(row => row.timestamp),
                datasets: [
                    {
                        label: sensorKey,
                        data: rawData.map(row => row[sensorKey]),
                        borderColor: 'blue',
                        fill: false,
                        // For compatibility with your code:
                        "ai data": rawData.map(row => row[sensorKey]) // Placeholder, replace with real AI data if available
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true }
                }
            }
        };
    });
}

async function updateView(type, rawData = null) {
    pageHeader.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Sensors`;

    if (!rawData) {
        rawData = await fetchData();
    }
    if (!rawData || rawData.length === 0) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    // Only create charts if they don't exist yet
    if (charts.length === 0) {
        clearCharts();
        const filteredSensors = transformBackendData(rawData, type);

        filteredSensors.forEach((sensorData, i) => {
            const card = document.createElement('div');
            card.style.marginBottom = '40px';
            card.innerHTML = `
                <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">${sensorData.data.datasets[0].label}</h2>
                <h3 id="latestData${i}" style="text-align:center; margin-bottom: 10px;"></h3>
                <canvas id="lineChart${i}"></canvas>
            `;
            chartsContainer.appendChild(card);

            const ctx = document.getElementById(`lineChart${i}`).getContext('2d');
            const chart = new Chart(ctx, {
                type: sensorData.type,
                data: {
                    labels: [],
                    datasets: [
                        { label: `${sensorData.data.datasets[0].label} (Actual)`, data: [], borderColor: 'blue', fill: false },
                        { label: `${sensorData.data.datasets[0].label} (AI Predicted)`, data: [], borderColor: 'red', fill: false }
                    ]
                },
                options: sensorData.options
            });
            charts.push(chart);
        });
    }

    // Update chart data
    const filteredSensors = transformBackendData(rawData, type);
    filteredSensors.forEach((sensorData, i) => {
        const normalData = sensorData.data.datasets[0].data.slice(-10);
        const aiData = sensorData.data.datasets[0]["ai data"].slice(-10);
        const labels = sensorData.data.labels.slice(-10);

        charts[i].data.labels = labels;
        charts[i].data.datasets[0].data = normalData;
        charts[i].data.datasets[1].data = aiData;
        charts[i].update();

        // Update latest data text
        const latestData = normalData.slice(-1)[0] ?? 'N/A';
        const latestDataElem = document.getElementById(`latestData${i}`);
        if (latestDataElem) latestDataElem.textContent = `Latest Data: ${latestData}`;
    });
}

async function checkForNewData() {
    try {
        const response = await fetch('http://localhost:5000/api/real_sensor_data');
        if (!response.ok) return;
        const data = await response.json();
        if (data && data.length > 0) {
            const newestTimestamp = data[data.length - 1].timestamp;
            if (lastTimestamp !== newestTimestamp) {
                lastTimestamp = newestTimestamp;
                updateView(currentView, data); // Pass data to avoid double fetch
            }
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

let currentView = 'flow'; // Track the current view

document.addEventListener('DOMContentLoaded', () => {
    const initialView = getQueryParam('view') || 'flow';
    currentView = initialView; // Set initial view
    console.log('Initial view from URL param:', initialView);

    if (initialView === 'flow') {
        activateButton(flowButton, pressureButton);
    } else if (initialView === 'pressure') {
        activateButton(pressureButton, flowButton);
    } else {
        // fallback
        activateButton(flowButton, pressureButton);
    }

    updateView(initialView);
});

flowButton.addEventListener('click', () => {
    console.log('Flow button clicked');
    activateButton(flowButton, pressureButton);
    currentView = 'flow'; // Update current view
    updateView('flow');
});

pressureButton.addEventListener('click', () => {
    console.log('Pressure button clicked');
    activateButton(pressureButton, flowButton);
    currentView = 'pressure'; // Update current view
    updateView('pressure');
});

setInterval(checkForNewData, 1000); // Check every second
