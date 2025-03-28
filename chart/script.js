const intervalTime = 30000; // 10 seconds
document.addEventListener('DOMContentLoaded', async () => {
    const chartElements = [
        document.getElementById('lineChart1').getContext('2d'),
        document.getElementById('lineChart2').getContext('2d'),
        document.getElementById('lineChart3').getContext('2d'),
        document.getElementById('lineChart4').getContext('2d'),
        document.getElementById('lineChart5').getContext('2d')
    ];

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

    const data = await fetchData('http://localhost:3000/random');
    if (!data) {
        console.error('No data available to create charts');
        return;
    }

    const charts = chartElements.map((ctx, index) => {
        return new Chart(ctx, {
            type: data[index].type,
            data: {
                labels: data[index].data.labels,
                datasets: data[index].data.datasets // Use both datasets for each chart
            },
            options: data[index].options,
        });
    });

    setInterval(async () => {
        const updatedData = await fetchData('http://localhost:3000/random');
        if (updatedData) {
            charts.forEach((chart, index) => {
                chart.data.labels = updatedData[index].data.labels.slice(-10); // Keep only the last 10 labels
                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    dataset.data = updatedData[index].data.datasets[datasetIndex].data.slice(-10); // Update dataset data
                });
                chart.update();
            });
        }
    }, intervalTime); // Update every 10 seconds
});