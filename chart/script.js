document.addEventListener('DOMContentLoaded', async () => {
    const ctxLine = document.getElementById('lineChart').getContext('2d');

    async function fetchData() {
        try {
            const response = await fetch('data.json');
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

    const data = await fetchData();
    if (!data) {
        console.error('No data available to create chart');
        return;
    }

    new Chart(ctxLine, {
        type: 'line',
        data: data.data,
        options: data.options
    });
});
