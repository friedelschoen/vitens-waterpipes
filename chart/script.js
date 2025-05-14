console.clear();

const intervalTime = 10000; // in milliseconds

let charts = [];
let currentApiUrl = 'http://localhost:5000/real_sensor_data/sensor_1';
let chartElements = [];
let isNavigating = false; // Flag to track navigation state
let pausedCharts = new Set(); // Track paused charts

const cardSubTitles = [
    document.getElementById('cardSubTitle1'),
    document.getElementById('cardSubTitle2'),
    document.getElementById('cardSubTitle3'),
    document.getElementById('cardSubTitle4'),
    document.getElementById('cardSubTitle5')
];

document.addEventListener('DOMContentLoaded', async () => {
    const dropdownButton = document.getElementById('sensorDropdownButton');
    const dropdown = document.getElementById('sensorDropdown');
    const dropdownIcon = document.getElementById('sensorDropdownIcon');

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

    const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach((checkbox) => {
        const chartIndex = checkbox.getAttribute('data-sensor');
        const chartContainer = document.getElementById(`chartContainer${chartIndex}`);
        const isChecked = JSON.parse(localStorage.getItem(`chartState_${chartIndex}`)) ?? true;

        checkbox.checked = isChecked;
        chartContainer.style.display = isChecked ? 'block' : 'none';

        checkbox.addEventListener('change', () => {
            const chartIndex = checkbox.getAttribute('data-sensor');
            const chartContainer = document.getElementById(`chartContainer${chartIndex}`);
            if (checkbox.checked) {
                chartContainer.style.display = 'block';
                chartContainer.classList.add('fade-in');
                chartContainer.classList.remove('fade-out');
            } else {
                chartContainer.classList.add('fade-out');
                chartContainer.classList.remove('fade-in');
                setTimeout(() => {
                    chartContainer.style.display = 'none';
                }, 300);
            }

            localStorage.setItem(`chartState_${chartIndex}`, checkbox.checked);
        });
    });

    const flowButton = document.getElementById('flowButton');
    const pressureButton = document.getElementById('pressureButton');
    const pageHeader = document.getElementById('pageHeader');
    const cardTitles = [
        document.getElementById('cardTitle1'),
        document.getElementById('cardTitle2'),
        document.getElementById('cardTitle3'),
        document.getElementById('cardTitle4'),
        document.getElementById('cardTitle5')
    ];

    async function updateView(type) {
        pageHeader.textContent = `${type} Sensors`;
        cardTitles.forEach((title, index) => {
            title.textContent = `${type} Sensor ${index + 1}`;
        });

        currentApiUrl = type === 'Flow' ? 'http://localhost:3000/random' : 'http://localhost:3100/random';

        const data = await fetchData(currentApiUrl);
        if (!data) {
            console.error(`No data available for ${type}`);
            return;
        }

        // Update subtitles with the latest data
        cardSubTitles.forEach((subTitle, index) => {
            const latestData = data[index]?.data?.datasets[0]?.data?.slice(-1)[0] ?? 'N/A';
            subTitle.textContent = `Latest ${type} RealTime Data: ${latestData}`;
        });

        // Destroy existing charts
        charts.forEach(chart => chart.destroy());
        charts = [];

        // Create new charts with only the last 10 values
        charts = chartElements.map((ctx, index) => {
            return new Chart(ctx, {
                type: data[index].type,
                data: {
                    labels: data[index].data.labels.slice(-10), // Display only the last 10 labels
                    datasets: data[index].data.datasets.map(dataset => ({
                        ...dataset,
                        data: dataset.data.slice(-10) // Display only the last 10 data points
                    }))
                },
                options: data[index].options,
            });
        });
    }

    function setActiveButton(activeButton) {
        [flowButton, pressureButton].forEach(button => {
            button.classList.toggle('active', button === activeButton);
        });
    }

    chartElements = [
        document.getElementById('lineChart1').getContext('2d'),
        document.getElementById('lineChart2').getContext('2d'),
        document.getElementById('lineChart3').getContext('2d'),
        document.getElementById('lineChart4').getContext('2d'),
        document.getElementById('lineChart5').getContext('2d')
    ];

    flowButton.addEventListener('click', async () => {
        setActiveButton(flowButton);
        await updateView('Flow');
    });

    pressureButton.addEventListener('click', async () => {
        setActiveButton(pressureButton);
        await updateView('Pressure');
    });

    setActiveButton(flowButton);
    await updateView('Flow');
});

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch data:', error);
        return null;
    }
}

setInterval(async () => {
    const updatedData = await fetchData(currentApiUrl);
    if (updatedData) {
        charts.forEach((chart, index) => {
            if (pausedCharts.has(index)) return; // Skip updates for paused charts

            // Update chart with only the last 10 values
            chart.data.labels = updatedData[index].data.labels.slice(-10);
            chart.data.datasets.forEach((dataset, datasetIndex) => {
                dataset.data = updatedData[index].data.datasets[datasetIndex].data.slice(-10);
            });
            chart.update();
        });
    }
}, intervalTime);

