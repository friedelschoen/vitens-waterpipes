const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3100;

let currentTime = "";
let chartsData = [];

// Function to generate a random dataset
function generateRandomDataset(label, borderColor) {
    return {
        label: label,
        desc: label,
        data: [Math.floor(Math.random() * 101)],
        fill: false,
        borderColor: borderColor,
        tension: 0.0
    };
}

// Initialize charts data
function initializeChartsData() {
    chartsData = [
        {
            type: "line",
            data: {
                desc: "Chart 1",
                labels: ["0"],
                datasets: [
                    generateRandomDataset("Pressure Sensor 1 - Realtime", "rgb(255, 0, 0)"),
                    generateRandomDataset("Pressure Sensor 1 - Emulated", "rgb(0, 255, 0)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        },
        {
            type: "line",
            data: {
                desc: "Chart 2",
                labels: ["0"],
                datasets: [
                    generateRandomDataset("Pressure Sensor 2 - Realtime", "rgb(0, 0, 255)"),
                    generateRandomDataset("Pressure Sensor 2 - Emulated", "rgb(255, 165, 0)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        },
        {
            type: "line",
            data: {
                desc: "Chart 3",
                labels: ["0"],
                datasets: [
                    generateRandomDataset("Pressure Sensor 3 - Realtime", "rgb(128, 0, 128)"),
                    generateRandomDataset("Pressure Sensor 3 - Emulated", "rgb(0, 128, 128)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        },
        {
            type: "line",
            data: {
                desc: "Chart 4",
                labels: ["0"],
                datasets: [
                    generateRandomDataset("Pressure Sensor 4 - Realtime", "rgb(128, 128, 0)"),
                    generateRandomDataset("Pressure Sensor 4 - Emulated", "rgb(0, 0, 0)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        },
        {
            type: "line",
            data: {
                desc: "Chart 5",
                labels: ["0"],
                datasets: [
                    generateRandomDataset("Pressure Sensor 5 - Realtime", "rgb(255, 20, 147)"),
                    generateRandomDataset("Pressure Sensor 5 - Emulated", "rgb(70, 130, 180)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        }
    ];
}

// Update charts data at regular intervals
function updateChartsData() {
    const date = new Date();
    const hour = date.getHours().toString().padStart(2, "0");
    const min = date.getMinutes().toString().padStart(2, "0");
    const sec = date.getSeconds().toString().padStart(2, "0");
    currentTime = `${hour}:${min}:${sec}`;

    chartsData.forEach((chart) => {
        chart.data.labels.push(currentTime); // Append new time
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(Math.floor(Math.random() * 101)); // Append new data
        });
    });
}

initializeChartsData();
setInterval(updateChartsData, 10000); // Update data every 10 seconds

app.get("/random", (req, res) => {
    res.json(chartsData);
});

app.listen(PORT, () => {
    console.log("Server Listening on PORT:", PORT);
    console.log("CORS enabled for all origins");
    console.log("API available at http://localhost:" + PORT + "/random");
    console.log("Press Ctrl+C to stop the server");
});