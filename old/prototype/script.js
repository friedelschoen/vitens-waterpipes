import Chart from './node_modules/chart.js/auto';

async function fetchData() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        console.log(data);
        return data;
    } catch (error) {
        console.error('Failed to fetch data:', error);
        return null;
    }
}

async function createChart() {
    const data = await fetchData();
    if (!data) {
        console.error('No data available to create chart');
        return;
    }
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {
        type: data.type,
        data: data.data,
        options: data.options
    });
}

document.addEventListener('DOMContentLoaded', createChart);