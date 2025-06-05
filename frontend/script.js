console.clear();

const intervalTime = 10000; // in milliseconds

let charts = [];
let chartElements = [];
let currentApiUrl = 'http://localhost:5000/real_sensor_data/sensor_1';
let pausedCharts = new Set();

const valves = [
    { name: "Valve 1", status: "Open" },
    { name: "Valve 2", status: "Closed" },
    { name: "Valve 3", status: "Open" },
    { name: "Valve 4", status: "Closed" },
    { name: "Valve 5", status: "Open" },
];

const cardSubTitles = Array.from({ length: 5 }, (_, i) => document.getElementById(`cardSubTitle${i + 1}`));
const cardTitles = Array.from({ length: 5 }, (_, i) => document.getElementById(`cardTitle${i + 1}`));

const dropdownButton = document.getElementById('sensorDropdownButton');
const dropdown = document.getElementById('sensorDropdown');
const dropdownIcon = document.getElementById('sensorDropdownIcon');
const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');

const flowButton = document.getElementById('flowButton');
const pressureButton = document.getElementById('pressureButton');
const pageHeader = document.getElementById('pageHeader');

chartElements = Array.from({ length: 5 }, (_, i) => document.getElementById(`lineChart${i + 1}`).getContext('2d'));

document.addEventListener('DOMContentLoaded', async () => {
    setupDropdown();
    setupCheckboxListeners();
    setupSensorButtons();

    setActiveButton(flowButton);
    await updateView('Flow');
});

function setupDropdown() {
    dropdown.classList.add('hidden');
    dropdownIcon.style.transform = 'rotate(180deg)';

    dropdownButton.addEventListener('click', (event) => {
        event.stopPropagation();
        dropdown.classList.toggle('hidden');
        const isRotated = dropdownIcon.style.transform === 'rotate(180deg)';
        dropdownIcon.style.transform = isRotated ? 'rotate(0deg)' : 'rotate(180deg)';
    });

    document.addEventListener('click', (event) => {
        if (!dropdown.contains(event.target) && !dropdownButton.contains(event.target)) {
            dropdown.classList.add('hidden');
        }
    });
}

function setupCheckboxListeners() {
    checkboxes.forEach((checkbox) => {
        const chartIndex = checkbox.getAttribute('data-sensor');
        const chartContainer = document.getElementById(`chartContainer${chartIndex}`);
        const savedState = JSON.parse(localStorage.getItem(`chartState_${chartIndex}`));
        const isChecked = savedState ?? true;

        checkbox.checked = isChecked;
        chartContainer.style.display = isChecked ? 'block' : 'none';

        checkbox.addEventListener('change', () => {
            const isVisible = checkbox.checked;
            chartContainer.style.display = isVisible ? 'block' : 'none';
            chartContainer.classList.toggle('fade-in', isVisible);
            chartContainer.classList.toggle('fade-out', !isVisible);

            if (!isVisible) {
                setTimeout(() => chartContainer.style.display = 'none', 300);
            }

            localStorage.setItem(`chartState_${chartIndex}`, isVisible);
        });
    });
}

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
    cardTitles.forEach((title, i) => title.textContent = `${type} Sensor ${i + 1}`);

    currentApiUrl = 'http://localhost:5000/real_sensor_data/sensor_1';

    const data = await fetchData(currentApiUrl);
    if (!data) return console.error(`No data available for ${type}`);

    cardSubTitles.forEach((subTitle, i) => {
        const latestData = data[i]?.data?.datasets[0]?.data?.slice(-1)[0] ?? 'N/A';
        subTitle.textContent = `Latest ${type} RealTime Data: ${latestData}`;
    });

    charts.forEach(chart => chart.destroy());
    charts = [];

    charts = chartElements.map((ctx, i) => new Chart(ctx, {
        type: data[i].type,
        data: {
            labels: data[i].data.labels.slice(-10),
            datasets: data[i].data.datasets.map(dataset => ({
                ...dataset,
                data: dataset.data.slice(-10)
            }))
        },
        options: data[i].options,
    }));
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
