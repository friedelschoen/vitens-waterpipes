const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors({
    origin: "134.122.57.132", // of je frontend-poort
}));

app.use(express.json());

const PORT = process.env.PORT || 3000;

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
                    generateRandomDataset("Flow Sensor 1 - RealTime", "rgb(75, 192, 192)"),
                    generateRandomDataset("Flow Sensor 1 - Emulated", "rgb(192, 75, 192)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100
                    },
                    x: {
                        beginAtZero: false,
                        min: 0,
                        max: 10
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
                    generateRandomDataset("Flow Sensor 2 - RealTime", "rgb(255, 99, 132)"),
                    generateRandomDataset("Flow Sensor 2 - Emulated", "rgb(132, 99, 255)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100
                    },
                    x: {
                        beginAtZero: false,
                        min: 0,
                        max: 10
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
                    generateRandomDataset("Flow Sensor 3 - RealTime", "rgb(54, 162, 235)"),
                    generateRandomDataset("Flow Sensor 3 - Emulated", "rgb(235, 162, 54)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100
                    },
                    x: {
                        beginAtZero: false,
                        min: 0,
                        max: 10
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
                    generateRandomDataset("Flow Sensor 4 - RealTime", "rgb(255, 206, 86)"),
                    generateRandomDataset("Flow Sensor 4 - Emulated", "rgb(86, 206, 255)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100
                    },
                    x: {
                        beginAtZero: false,
                        min: 0,
                        max: 10
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
                    generateRandomDataset("Flow Sensor 5 - RealTime", "rgb(153, 102, 255)"),
                    generateRandomDataset("Flow Sensor 5 - Emulated", "rgb(255, 102, 153)")
                ]
            },
            options: {
                animation: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 100
                    },
                    x: {
                        beginAtZero: false,
                        min: 0,
                        max: 10
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