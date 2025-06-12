console.clear();

const intervalTime = 10000; // 10 seconden

let charts = [];
let currentApiUrl = 'http://localhost:5000/real_sensor_data/sensor_1';
let pausedCharts = new Set();

// Element references (deze *moeten* nog in je HTML staan)
const flowButton = document.getElementById('flowButton');
const pressureButton = document.getElementById('pressureButton');
const pageHeader = document.getElementById('pageHeader');
const chartsContainer = document.getElementById('charts'); // Lege div in je HTML

document.addEventListener('DOMContentLoaded', async () => {
    setupSensorButtons();
    setActiveButton(flowButton);
    await updateView('Flow');
});

function setupSensorButtons() {
    flowButton.addEventListener('click', async () => {
        setActiveButton(flowButton);
        await updateView('Flow');
    });

    pressureButton.addEventListener('click', async () => {
        setActiveButton(pressureButton);
        await updateView('Pressure');
    });
}

function setActiveButton(activeButton) {
    [flowButton, pressureButton].forEach(button => {
        button.classList.toggle('active', button === activeButton);
    });
}

async function updateView(type) {
    pageHeader.textContent = `${type} Sensors`;

    // Zet juiste API URL op basis van type (pas aan indien nodig)
    currentApiUrl = `http://localhost:5000/real_sensor_data/sensor_1`; // Of `/sensor_1_flow`, etc.

    const data = await fetchData(currentApiUrl);
    if (!data) {
        console.error(`No data available for ${type}`);
        return;
    }

    // Maak ruimte leeg en verwijder oude charts
    chartsContainer.innerHTML = '';
    charts.forEach(chart => chart.destroy());
    charts = [];

    // Maak een nieuwe chart card voor elk sensoritem
    data.forEach((sensorData, i) => {
        const chartCard = document.createElement('div');
        chartCard.id = `chartContainer${i}`;
        chartCard.className = 'bg-white p-6 rounded-lg shadow-lg';

        const title = document.createElement('h2');
        title.id = `cardTitle${i}`;
        title.className = 'text-2xl font-bold text-center mb-6 font-mono';
        title.textContent = `${type} Sensor ${i + 1}`;

        const subtitle = document.createElement('h3');
        subtitle.id = `cardSubTitle${i}`;
        subtitle.className = 'text-lg font-bold text-center mb-6 font-mono';
        const latestData = sensorData?.data?.datasets[0]?.data?.slice(-1)[0] ?? 'N/A';
        subtitle.textContent = `Latest ${type} RealTime Data: ${latestData}`;

        const canvas = document.createElement('canvas');
        canvas.id = `lineChart${i}`;
        const ctx = canvas.getContext('2d');

        chartCard.appendChild(title);
        chartCard.appendChild(subtitle);
        chartCard.appendChild(canvas);
        chartsContainer.appendChild(chartCard);

        // Bouw de chart op
        const chart = new Chart(ctx, {
            type: sensorData.type,
            data: {
                labels: sensorData.data.labels.slice(-10),
                datasets: sensorData.data.datasets.map(ds => ({
                    ...ds,
                    data: ds.data.slice(-10),
                })),
            },
            options: sensorData.options,
        });

        charts.push(chart);
    });
}

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch data:', error);
        return null;
    }
}

// Realtime update van grafiekdata elke 10 seconden
setInterval(async () => {
    const updatedData = await fetchData(currentApiUrl);
    if (!updatedData) return;

    charts.forEach((chart, i) => {
        if (pausedCharts.has(i)) return;

        chart.data.labels = updatedData[i].data.labels.slice(-10);
        chart.data.datasets.forEach((dataset, j) => {
            dataset.data = updatedData[i].data.datasets[j].data.slice(-10);
        });
        chart.update();
    });
}, intervalTime);
