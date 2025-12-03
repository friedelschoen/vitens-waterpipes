// -----------------------------
// Globals & DOM references
// -----------------------------

let charts = [];
let lastTimestamp = null; // Track newest timestamp to fetch/update correctly
const limit = 100; // Max number of data points retained per chart

const chartsContainer = document.getElementById("chartsContainer");
const valvesContainer = document.getElementById("valves-div");

// Normaliseer valve-state (1, "1", true, "open" → open)
function isValveOpen(state) {
    return state === 1 || state === "1" || state === true || state === "open";
}

// -----------------------------
// API calls
// -----------------------------

async function fetchSensors() {
    try {
        const response = await fetch(`/api/sensors`);
        if (!response.ok) throw new Error("Network response not ok");
        return await response.json();
    } catch (error) {
        console.error("Fetch sensor data error:", error);
        return null;
    }
}

async function fetchSensorData() {
    try {
        const response = await fetch(`/api/sensor_data?limit=${limit}`);
        if (!response.ok) throw new Error("Network response not ok");
        return await response.json();
    } catch (error) {
        console.error("Fetch sensor data error:", error);
        return null;
    }
}

async function fetchValves() {
    try {
        const response = await fetch(`/api/get_valves`);
        if (!response.ok) throw new Error("Network response not ok");
        return await response.json();
    } catch (error) {
        console.error("Fetch valves error:", error);
        return null;
    }
}

async function setValveState(valve, state) {
    let res = await fetch("/api/set_valve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ valve, state }),
    });
    let result = await res.json();
    if (result.error) {
        throw res.error;
    }
    return;
}

// -----------------------------
// Chart management
// -----------------------------

function clearCharts() {
    charts.forEach(({ chart }) => chart.destroy?.());
    charts = [];
    chartsContainer.innerHTML = "";
}

/**
 * Maak een kaart + Chart.js instance voor één sensor
 */
function createChartForSensor(sensorKey, index, allData) {
    const card = document.createElement("div");
    card.style.marginBottom = "40px";

    const latestId = `latest-data-${index}`;
    const canvasId = `lineChart${index}`;

    card.innerHTML = `
        <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">
            ${sensorKey.name}
        </h2>
        <h3 style="text-align:center; margin-bottom: 10px;"><span id="${latestId}">N/A</span> ${sensorKey.unit}</h3>
        <canvas id="${canvasId}"></canvas>
    `;

    chartsContainer.appendChild(card);

    const ctx = document.getElementById(canvasId).getContext("2d");

    const initialActualData = allData
        .map((row) => {
            const sensor = row.sensors[sensorKey.name];
            return sensor && typeof sensor.value !== "undefined"
                ? { x: row.timestamp, y: sensor.value }
                : null;
        })
        .filter((x) => x);

    const datasets = [
        {
            label: `${sensorKey.name} (Actual)`,
            data: initialActualData,
            borderColor: "blue",
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0,
        },
    ];

    const chart = new Chart(ctx, {
        type: "line",
        data: {
            // labels: initialLabels,
            datasets,
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true },
            },
            scales: {
                x: {
                    type: "linear",
                    bounds: "data",
                    ticks: {
                        callback(value) {
                            const d = new Date(value * 1000);
                            return d.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                                second: "2-digit",
                                hour12: false,
                            });
                        },
                    },
                },
                y: {
                    beginAtZero: true,
                },
            },
        },
    });

    const latestDataEl = document.getElementById(latestId);
    const latestValue = initialActualData[initialActualData.length - 1];
    latestDataEl.textContent = `Latest Data: ${
        latestValue?.y?.toFixed(2) ?? "N/A"
    }`;

    charts.push({ chart, sensorKey: sensorKey.name, latestDataEl });
}

/**
 * Initialiseer alle charts op basis van huidige data
 * Wordt gebruikt bij page load of view-switch.
 */
async function initializeCharts() {
    const sensors = await fetchSensors();

    const allData = await fetchSensorData();
    if (!allData || allData.length === 0) {
        chartsContainer.innerHTML = `<p>No data available</p>`;
        return;
    }

    // Bepaal alle sensoren uit de eerste rij
    sensors.sort();

    clearCharts();

    lastTimestamp = allData[allData.length - 1].timestamp;

    sensors.forEach((sensorKey, i) => {
        console.log(sensorKey);
        createChartForSensor(sensorKey, i, allData);
    });
}

/**
 * Haal nieuwe data op en schuif de bestaande charts door
 */
async function updateChartData() {
    // Als charts nog niet zijn opgebouwd (of geen data), doe niks
    if (!lastTimestamp) return;

    const newData = await fetchSensorData();
    if (!newData || newData.length === 0) return;

    // Alleen punten met een nieuwere timestamp dan lastTimestamp
    const newPoints = newData.filter((row) => row.timestamp > lastTimestamp);
    if (newPoints.length === 0) return;

    lastTimestamp = newPoints[newPoints.length - 1].timestamp;

    charts.forEach(({ chart, sensorKey, latestDataEl }) => {
        newPoints.forEach((row) => {
            const sensor = row.sensors[sensorKey];
            const value =
                sensor && typeof sensor.value !== "undefined"
                    ? sensor.value
                    : null;

            chart.data.datasets[0].data.push({ x: row.timestamp, y: value });
        });

        // Sliding window op basis van limit
        while (chart.data.datasets[0].data.length > limit) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        const latestValue =
            chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
        latestDataEl.textContent = `Latest Data: ${
            latestValue?.y?.toFixed(2) ?? "N/A"
        }`;

        chart.update();
    });
}

// -----------------------------
// Valves UI
// -----------------------------

function updateValveText(valve, state) {
    const stateSpan = document.getElementById(`valve-state-${valve}`);
    const openBtn = document.getElementById(`open-btn-${valve}`);
    const closeBtn = document.getElementById(`close-btn-${valve}`);

    const open = isValveOpen(state);

    // Update tekst + kleur
    if (stateSpan) {
        stateSpan.classList.remove(
            "text-green-500",
            "text-red-400",
            "text-black",
            "font-bold",
            "font-semibold"
        );

        if (open) {
            stateSpan.textContent = "open";
            stateSpan.classList.add("text-green-500", "font-bold");
        } else {
            stateSpan.textContent = "closed";
            stateSpan.classList.add("text-red-400", "font-bold");
        }
    }

    // Update button-styling
    if (openBtn && closeBtn) {
        openBtn.disabled = false;
        closeBtn.disabled = false;

        openBtn.classList.remove(
            "bg-green-500",
            "text-white",
            "font-bold",
            "ring",
            "ring-green-300",
            "bg-neutral-700",
            "hover:bg-neutral-800",
            "bg-gray-300",
            "hover:bg-gray-400",
            "text-gray-800"
        );
        closeBtn.classList.remove(
            "bg-red-500",
            "text-white",
            "font-bold",
            "ring",
            "ring-red-300",
            "bg-gray-300",
            "hover:bg-gray-400",
            "text-gray-800",
            "bg-neutral-700",
            "hover:bg-neutral-800"
        );

        if (open) {
            openBtn.classList.add(
                "bg-green-500",
                "text-white",
                "font-bold",
                "ring",
                "ring-green-300"
            );
            closeBtn.classList.add(
                "bg-gray-300",
                "hover:bg-gray-400",
                "text-gray-800"
            );
        } else {
            closeBtn.classList.add(
                "bg-red-500",
                "text-white",
                "font-bold",
                "ring",
                "ring-red-300"
            );
            openBtn.classList.add(
                "bg-gray-300",
                "hover:bg-gray-400",
                "text-gray-800"
            );
        }
    }
}

function handleValveButtonClick(e) {
    const target = e.currentTarget;
    const valve = target.getAttribute("data-valve");
    const action = target.getAttribute("data-action"); // "open" of "close"

    if (!valve || !action) return;

    setValveState(valve, action).then(() => updateValveText(valve, action));
}

async function createValves() {
    const valves = await fetchValves();
    if (!valves || typeof valves !== "object") {
        console.warn("No valves data received");
        return;
    }

    valvesContainer.innerHTML = "";

    for (const name in valves) {
        if (!Object.prototype.hasOwnProperty.call(valves, name)) continue;

        const wrapper = document.createElement("div");
        wrapper.className =
            "bg-white rounded-xl mt-4 p-6 w-72 shadow-md flex flex-col items-center";
        wrapper.innerHTML = `
            <h2 class="text-xl font-semibold mb-2 text-gray-800">${name}</h2>
            <p class="mb-4 text-gray-500">
                Valve is now
                <span id="valve-state-${name}" class="font-semibold text-red-400">closed</span>
            </p>
            <div class="flex gap-4">
                <button
                    class="bg-neutral-700 hover:bg-neutral-800 text-white font-medium py-2 px-5 rounded transition"
                    data-valve="${name}"
                    data-action="open"
                    id="open-btn-${name}">
                    Open
                </button>
                <button
                    class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-5 rounded transition"
                    data-valve="${name}"
                    data-action="close"
                    id="close-btn-${name}">
                    Close
                </button>
            </div>
        `;

        valvesContainer.appendChild(wrapper);

        // Init state vanuit backend
        updateValveText(name, valves[name]);

        // Event listeners
        const openBtn = document.getElementById(`open-btn-${name}`);
        const closeBtn = document.getElementById(`close-btn-${name}`);

        openBtn.addEventListener("click", handleValveButtonClick);
        closeBtn.addEventListener("click", handleValveButtonClick);
    }
}

// -----------------------------
// Init
// -----------------------------

document.addEventListener("DOMContentLoaded", () => {
    initializeCharts();
    createValves();

    setInterval(updateChartData, 2000);
});
