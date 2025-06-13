let charts = [];
let allData = null;

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
    if (allData) return allData; // cache data
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error('Network response not ok');
        allData = await response.json();
        return allData;
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

async function updateView(type) {
    pageHeader.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Sensors`;

    const data = await fetchData();

    if (!data) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    // Deze functie MOET boven updateView staan in je script
    clearCharts(); // Zorg ervoor dat dit hierboven gedefinieerd is

    const filteredSensors = data.filter(sensor =>
        sensor.data.datasets[0].label.toLowerCase().includes(type.toLowerCase())
    );

    filteredSensors.forEach((sensorData, i) => {
        const normalData = sensorData.data.datasets[0].data.slice(-10);
        const aiData = sensorData.data.datasets[0]["ai data"].slice(-10);
        const labels = sensorData.data.labels.slice(-10);
        const baseLabel = sensorData.data.datasets[0].label;

        const latestData = normalData.slice(-1)[0] ?? 'N/A';

        const card = document.createElement('div');
        card.style.marginBottom = '40px';

        card.innerHTML = `
            <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">${baseLabel}</h2>
            <h3 style="text-align:center; margin-bottom: 10px;">Latest Data: ${latestData}</h3>
            <canvas id="lineChart${i}"></canvas>
        `;

        chartsContainer.appendChild(card);

        const ctx = document.getElementById(`lineChart${i}`).getContext('2d');

        const chart = new Chart(ctx, {
            type: sensorData.type,
            data: {
                labels,
                datasets: [
                    {
                        label: `${baseLabel} (Actual)`,
                        data: normalData,
                        borderColor: 'blue',
                        fill: false
                    },
                    {
                        label: `${baseLabel} (AI Predicted)`,
                        data: aiData,
                        borderColor: 'red',
                        fill: false
                    }
                ]
            },
            options: sensorData.options
        });

        charts.push(chart);
    });
}


document.addEventListener('DOMContentLoaded', () => {
    const initialView = getQueryParam('view') || 'flow';
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
    updateView('flow');
});

pressureButton.addEventListener('click', () => {
    console.log('Pressure button clicked');
    activateButton(pressureButton, flowButton);
    updateView('pressure');
});
