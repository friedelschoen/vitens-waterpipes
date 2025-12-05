// -----------------------------
// Globals & DOM references
// -----------------------------

let charts = [];
let lastTimestamp = null; // Track newest timestamp to fetch/update correctly
let collectorActive = false;
const sinceseconds = 120; // = 2 minute; Max number of data points retained per chart

const chartsContainer = document.getElementById("chartsContainer");
const valvesContainer = document.getElementById("valves-div");

// Normaliseer valve-state (1, "1", true, "open" → open)
function isValveOpen(state) {
    return state === 1 || state === "1" || state === true || state === "open";
}

// -----------------------------
// API calls
// -----------------------------

async function apiCall(endpoint, method = "GET", body = {}) {
    let params = { method: method };
    if (method != "GET" && method != "HEAD") {
        params.headers = { "Content-Type": "application/json" };
        params.body = JSON.stringify(body);
    }
    let res = await fetch(endpoint, params);
    let result = await res.json();
    if (result.error) {
        throw new Error(res.error);
    }
    return result;
}

function fetchSensors() {
    return apiCall("/api/sensors");
}

function fetchSensorData() {
    return apiCall(`/api/sensor_data?since=${Date.now() / 1000}`);
}

function fetchValves() {
    return apiCall(`/api/get_valves`);
}

function setValveState(valve, state) {
    return apiCall(`/api/set_valves`, "POST", { valve, state });
}

function startCollector() {
    return apiCall(`/api/start_collector`, "POST");
}

function cancelCollector() {
    return apiCall(`/api/cancel_collector`, "POST");
}

function fetchCollector() {
    return apiCall(`/api/get_collector`);
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
function createChartForSensor(sensorKey, index, allData, predictors) {
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

    let datasets = predictors.map((name) => ({
        label:
            name == "none"
                ? `${sensorKey.name} (Actual)`
                : `${name} (Predicted)`,
        data: allData[name].map((row) => ({
            x: row.timestamp,
            y: row.sensors[sensorKey.name].value,
        })),
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
    }));

    const chart = new Chart(ctx, {
        type: "line",
        data: {
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
    const latestValue = allData.none[allData.none.length - 1];
    latestDataEl.textContent = `Latest Data: ${
        latestValue?.y?.toFixed(2) ?? "N/A"
    }`;

    charts.push({
        chart,
        sensorKey: sensorKey.name,
        latestDataEl,
        predictors,
    });
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

    clearCharts();

    lastTimestamp = allData.none[allData.none.length - 1].timestamp;

    sensors.sensors.forEach((sensorKey, i) =>
        createChartForSensor(sensorKey, i, allData, sensors.predictors)
    );
}

/**
 * Haal nieuwe data op en schuif de bestaande charts door
 */
async function update() {
    // Als charts nog niet zijn opgebouwd (of geen data), doe niks
    if (!lastTimestamp) return;

    const newData = await fetchSensorData();
    if (!newData || newData.length === 0) return;

    charts.forEach(({ chart, sensorKey, latestDataEl, predictors }) => {
        for (let predname in newData) {
            let index = predictors.indexOf(predname);
            for (let row of newData[predname]) {
                if (row.timestamp <= lastTimestamp) continue;

                const sensor = row.sensors[sensorKey];
                const value =
                    sensor && typeof sensor.value !== "undefined"
                        ? sensor.value
                        : null;

                chart.data.datasets[index].data.push({
                    x: row.timestamp,
                    y: value,
                });
            }

            let since = Date.now() / 1000 - sinceseconds;
            while (chart.data.datasets[index].data[0].x < since) {
                chart.data.datasets[index].data.shift();
            }
        }

        const latestValue =
            chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
        latestDataEl.textContent = `Latest Data: ${
            latestValue?.y?.toFixed(2) ?? "N/A"
        }`;

        chart.update();
    });

    lastTimestamp = newData.none[newData.none.length - 1].timestamp;

    const valves = await fetchValves();
    for (let name in valves) {
        updateValveText(name, valves[name]);
    }

    const collector = await fetchCollector();
    if (collector.active) {
        console.log(collector);
        if (!collectorActive) {
            activateCollector();
        }

        const progress = document.getElementById("collector-progress");
        const percent = Math.floor(collector.progress * 100);
        const min = Math.round(collector.time / 60);
        const sec = Math.round(collector.time) % 60;
        const secstr = sec.toString().padStart(2, "0");
        progress.classList.remove("hidden");
        progress.innerHTML = `${percent}% &mdash; ${min}:${secstr} left`;

        const dbname = document.getElementById("collector-dbname");
        dbname.innerText = " " + collector.dbname;
    } else {
        if (collectorActive) {
            deactivateCollector();
        }
    }
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

function activateCollector() {
    collectorActive = true;
    const btn = document.getElementById("collector-btn");
    btn.innerText = "Cancel";
    btn.classList.add("bg-gray-800");
    btn.classList.remove("bg-red-500");

    const stateSpan = document.getElementById("collector-state");
    stateSpan.innerHTML = "active";
    stateSpan.classList.add("text-green-300");
    stateSpan.classList.remove("text-red-400");
}

function deactivateCollector() {
    collectorActive = false;
    const btn = document.getElementById("collector-btn");
    btn.innerText = "Record";
    btn.classList.add("bg-red-500");
    btn.classList.remove("bg-gray-800");

    const stateSpan = document.getElementById("collector-state");
    stateSpan.innerHTML = "inactive";
    stateSpan.classList.add("text-red-400");
    stateSpan.classList.remove("text-green-300");

    const progress = document.getElementById("collector-progress");
    progress.classList.add("hidden");

    const dbname = document.getElementById("collector-dbname");
    dbname.innerText = "";
}

function handleCollectorRecord() {
    if (!collectorActive) {
        startCollector().then(activateCollector).catch(console.error);
    } else {
        cancelCollector().then(deactivateCollector).catch(console.error);
    }
}

async function createValves() {
    const valves = await fetchValves();
    if (!valves || typeof valves !== "object") {
        console.warn("No valves data received");
        return;
    }

    // valvesContainer.innerHTML = "";

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

document
    .getElementById("collector-btn")
    .addEventListener("click", handleCollectorRecord);

document.addEventListener("DOMContentLoaded", () => {
    initializeCharts();
    createValves();

    setInterval(update, 1500);
});
