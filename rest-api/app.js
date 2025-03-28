const express = require("express");
const cors = require("cors"); // Import CORS middleware

const app = express();
app.use(cors()); // Enable CORS
app.use(express.json());

const PORT = process.env.PORT || 3000;

setInterval(() => {
    date = new Date();
    hour = date.getHours();
    min = date.getMinutes();
    sec = date.getSeconds();
    if (hour < 10) {
        hour = "0" + hour; // Add leading zero to hours if less than 10
    }
    if (min < 10) {
        min = "0" + min; // Add leading zero to minutes if less than 10
    }
    if (sec < 10) {
        sec = "0" + sec; // Add leading zero to seconds if less than 10
    }
    return hour, min, sec; // Return formatted time
}, 1000);

// Function to generate a random dataset
function generateRandomDataset(label, borderColor) {
    return {
        label: label,
        desc: label,
        data: [Math.floor(Math.random() * 101)], // Initial random value
        fill: false,
        borderColor: borderColor,
        tension: 0.0
    };
}

let chartsData = [
    {
        type: "line",
        data: {
            desc: "Chart 1",
            labels: ["0"],
            datasets: [
                generateRandomDataset("Flow Sensor 1 - Line 1", "rgb(75, 192, 192)"),
                generateRandomDataset("Flow Sensor 1 - Line 2", "rgb(192, 75, 192)")
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
                generateRandomDataset("Flow Sensor 2 - Line 1", "rgb(255, 99, 132)"),
                generateRandomDataset("Flow Sensor 2 - Line 2", "rgb(132, 99, 255)")
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
                generateRandomDataset("Flow Sensor 3 - Line 1", "rgb(54, 162, 235)"),
                generateRandomDataset("Flow Sensor 3 - Line 2", "rgb(235, 162, 54)")
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
                generateRandomDataset("Flow Sensor 4 - Line 1", "rgb(255, 206, 86)"),
                generateRandomDataset("Flow Sensor 4 - Line 2", "rgb(86, 206, 255)")
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
                generateRandomDataset("Flow Sensor 5 - Line 1", "rgb(153, 102, 255)"),
                generateRandomDataset("Flow Sensor 5 - Line 2", "rgb(255, 102, 153)")
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

// Route to generate new random data for all charts
app.get("/random", (req, res) => {
    chartsData.forEach((chart) => {
        // const currentHour = chart.data.labels.length; // Determine the next hour
        chart.data.labels.push(`${hour}:${min}:${sec}`) //add new label

        // Generate a new random value for each dataset in the chart
        chart.data.datasets.forEach((dataset) => {
            dataset.data.push(Math.floor(Math.random() * 101)); // Random value between 0 and 100
        });
    });

    res.json(chartsData); // Send updated data for all charts as response
});

app.listen(PORT, () => {
    console.log("Server Listening on PORT:", PORT);
    console.log("CORS enabled for all origins");
    console.log("API available at http://localhost:" + PORT + "/random");
    console.log("Press Ctrl+C to stop the server");
});