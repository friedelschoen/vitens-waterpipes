// -----------------------------
// Globals & DOM references
// -----------------------------

const sinceseconds = 60; // = 2 minute; Max number of data points retained per chart

let charts = [];
let lastTimestamp = null; // Track newest timestamp to fetch/update correctly
let collectorActive = false;
let replayActive = false;

const chartsContainer = document.getElementById("chartsContainer");
const valvesContainer = document.getElementById("valves-div");

// interval id for main view refreshing
let mainInterval = null;

// -----------------------------
// API calls
// -----------------------------

async function apiCall(endpoint, method = "GET", body = {}) {
    let params = { method: method };
    if (method != "GET" && method != "HEAD") {
        params.headers = { "Content-Type": "application/json" };
        params.body = JSON.stringify(body);
    }
    let resp = await fetch(endpoint, params);
    let result = await resp.json();
    if (result.error) {
        throw new Error(result.error);
    }
    return result;
}

function fetchSensors() {
    return apiCall("/api/sensors");
}

function fetchSensorData(since) {
    return apiCall(`/api/sensor_data?since=${since}`);
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

function doReplay(time) {
    return apiCall(`/api/replay?since=${time}`, "POST");
}

function cancelReplay() {
    return apiCall(`/api/cancel_replay`, "POST");
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
                    max: 5,
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
    applySensorPositions(sensors);
    const sensorData = await fetchSensorData(Date.now() / 1000 - sinceseconds);
    const allData = sensorData.values;
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

    const sensorData = await fetchSensorData(lastTimestamp);
    const newData = sensorData.values;
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
        updateValveText(name, valves[name].state, valves[name].wants);
    }

    const collector = await fetchCollector();
    if (collector.active) {
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

    if (sensorData.replay) {
        if (!replayActive) {
            activateReplay();
        }

        const progress = document.getElementById("replay-progress");
        const timestr = new Date(
            sensorData.replay.timestamp * 1000
        ).toLocaleTimeString([], {
            day: "2-digit",
            month: "2-digit",
            year: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        });
        const percent = (sensorData.replay.progress * 100).toFixed(1);

        progress.classList.remove("hidden");
        progress.innerHTML = `${percent}% &mdash; replaying at ${timestr}`;
    } else {
        if (replayActive) {
            deactivateReplay();
        }
    }
}

// -----------------------------
// Valves UI
// -----------------------------

function updateValveText(valve, current, wants) {
    const div = document.getElementById(`valve-${valve}`);
    const stateSpan = document.getElementById(`valve-state-${valve}`);
    const openBtn = document.getElementById(`open-btn-${valve}`);
    const closeBtn = document.getElementById(`close-btn-${valve}`);

    const open = current == "open";
    const wantsOpen = wants == "open";

    if (current !== wants) {
        div.classList.add("bg-red-100");
        div.classList.remove("bg-white");
    } else {
        div.classList.add("bg-white");
        div.classList.remove("bg-red-100");
    }

    stateSpan.classList.remove(
        "text-green-500",
        "text-red-400",
        "text-black",
        "font-bold",
        "font-semibold"
    );

    if (open) {
        stateSpan.innerHTML = `Valve is now <span class="text-green-500">open</span>`;
        if (!wantsOpen) {
            stateSpan.innerHTML += `<b>, but wants <span class="text-red-400">closed</span></b>`;
        }
    } else {
        stateSpan.innerHTML = `Valve is now <span class="text-red-400">closed</span>`;
        if (wantsOpen) {
            stateSpan.innerHTML += `<b>, but wants <span class="text-green-400">open</span></b>`;
        }
    }

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
        "text-gray-800",
        "animate-pulse"
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
        "hover:bg-neutral-800",
        "animate-pulse"
    );

    if (wantsOpen) {
        openBtn.classList.add(
            "bg-green-500",
            "text-white",
            "font-bold",
            "ring",
            "ring-green-300"
        );
        if (!open) {
            openBtn.classList.add("animate-pulse");
        }
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
        if (open) {
            closeBtn.classList.add("animate-pulse");
        }
        openBtn.classList.add(
            "bg-gray-300",
            "hover:bg-gray-400",
            "text-gray-800"
        );
    }
}

function handleValveButtonClick(e) {
    const target = e.currentTarget;
    const valve = target.getAttribute("data-valve");
    const action = target.getAttribute("data-action"); // "open" of "close"

    if (!valve || !action) return;

    setValveState(valve, action)
        .then(() => updateValveText(valve, action, action))
        .catch(console.error);
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
    stateSpan.classList.remove("text-gray-700");
}

function deactivateCollector() {
    collectorActive = false;
    const btn = document.getElementById("collector-btn");
    btn.innerText = "Record";
    btn.classList.add("bg-red-500");
    btn.classList.remove("bg-gray-800");

    const stateSpan = document.getElementById("collector-state");
    stateSpan.innerHTML = "inactive";
    stateSpan.classList.add("text-gray-700");
    stateSpan.classList.remove("text-green-300");

    const progress = document.getElementById("collector-progress");
    progress.classList.add("hidden");

    const dbname = document.getElementById("collector-dbname");
    dbname.innerText = "";
}

function activateReplay() {
    replayActive = true;
    const btn = document.getElementById("replay-btn");
    btn.value = "Stop";
    btn.classList.add("bg-gray-800");
    btn.classList.remove("bg-yellow-500");

    const stateSpan = document.getElementById("replay-state");
    stateSpan.innerHTML = "active";
    stateSpan.classList.add("text-yellow-300");
    stateSpan.classList.remove("text-gray-700");
}

function deactivateReplay() {
    replayActive = false;
    const btn = document.getElementById("replay-btn");
    btn.value = "Replay";
    btn.classList.add("bg-yellow-500");
    btn.classList.remove("bg-gray-800");

    const stateSpan = document.getElementById("replay-state");
    stateSpan.innerHTML = "inactive";
    stateSpan.classList.add("text-yellow-400");
    stateSpan.classList.remove("text-gray-700");

    const progress = document.getElementById("replay-progress");
    progress.classList.add("hidden");
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

    for (const name in valves) {
        const wrapper = document.createElement("div");
        wrapper.id = `valve-${name}`;
        wrapper.className =
            "bg-white rounded-xl mt-4 p-6 w-72 shadow-md flex flex-col items-center";
        wrapper.innerHTML = `
            <h2 class="text-xl font-semibold mb-2 text-gray-800">${name}</h2>
            <p id="valve-state-${name}" class="mb-4 text-gray-500">
                Valve is now
                <span class="font-semibold text-red-400">closed</span>
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
        updateValveText(name, valves[name].state, valves[name].wants);

        // Event listeners
        const openBtn = document.getElementById(`open-btn-${name}`);
        const closeBtn = document.getElementById(`close-btn-${name}`);

        openBtn.addEventListener("click", handleValveButtonClick);
        closeBtn.addEventListener("click", handleValveButtonClick);
    }
}

async function handleReplay(event) {
    event.preventDefault();

    if (!replayActive) {
        const timeForm = document.getElementById("replay-time");
        const timestamp = Date.parse(timeForm.value);
        doReplay(timestamp).then(activateReplay).catch(console.error);
    } else {
        cancelReplay().then(deactivateReplay).catch(console.error);
    }
}

// sensor position map (percentages relative to image)
// keys include the exact API-style names (no spaces, lowercase) and human variants will be matched too.
const SENSOR_POSITIONS = {
    // top layer
    "flow0": { x: 21, y: 6 },
    "flow1": { x: 8, y: 49 },
    "pressure0": { x: 5, y: 25 },
    "pressure1": { x: 80, y: 25 },

    // bottom layer
    "flow2": { x: 30, y: 75 },
    "flow3": { x: 50, y: 85 },
    "flow4": { x: 70, y: 75 },
    "pressure2": { x: 20, y: 65 },
    "pressure3": { x: 50, y: 75 },
    "pressure4": { x: 80, y: 65 },
    "pressure5": { x: 90, y: 80 },
};

/**
 * Apply client-side positions for sensors if API doesn't provide x/y.
 * Mutates sensors.sensors array items to add x,y.
 */
function applySensorPositions(sensors) {
    if (!sensors || !Array.isArray(sensors.sensors)) return;

    // Normalized lookup: remove non-alphanumeric and lowercase
    const normalize = (s) => String(s ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const lookup = {};
    for (const k in SENSOR_POSITIONS) {
        lookup[normalize(k)] = SENSOR_POSITIONS[k];
    }

    sensors.sensors.forEach((s) => {
        if (!s || typeof s.name !== "string") return;
        const keyNorm = normalize(s.name);
        const pos = lookup[keyNorm] || SENSOR_POSITIONS[s.name] || SENSOR_POSITIONS[s.name.trim()];
        if (pos && (typeof s.x !== "number" || typeof s.y !== "number")) {
            s.x = Number(pos.x);
            s.y = Number(pos.y);
        }
    });
}

// Render map of sensorName -> latest value into a given element
function renderOverlay(elementId, sensorsSlice, allData) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!allData || !allData.none || allData.none.length === 0) {
        el.innerHTML = "<div class=\"text-sm text-gray-600 p-2\">No recent data</div>";
        return;
    }

    // use the newest row in the 'none' predictor as the most recent timestamp
    const latestRow = allData.none[allData.none.length - 1];

    // clear previous sensor badges
    el.innerHTML = "";

    sensorsSlice.forEach((sensorKey) => {
        const name = sensorKey.name;
        const unit = sensorKey.unit ?? "";
        const sensor = latestRow.sensors?.[name];
        const rawVal =
            sensor && typeof sensor.value !== "undefined"
                ? sensor.value
                : null;
        const value =
            rawVal === null || typeof rawVal === "undefined"
                ? "N/A"
                : (typeof rawVal === "number" ? rawVal.toFixed(2) : String(rawVal));

        // coerce x/y to numbers; tolerate string values and fallbacks
        const maybeNumber = (v) => {
            if (typeof v === "number" && isFinite(v)) return v;
            if (typeof v === "string" && v.trim() !== "") {
                const n = Number(v);
                if (isFinite(n)) return n;
            }
            return null;
        };

        const xnum = maybeNumber(sensorKey.x) ?? maybeNumber(sensorKey.left) ?? null;
        const ynum = maybeNumber(sensorKey.y) ?? maybeNumber(sensorKey.top) ?? null;

        const x = xnum !== null ? xnum : 10;
        const y = ynum !== null ? ynum : 10;

        const wrapper = document.createElement("div");
        wrapper.className = "absolute transform -translate-x-1/2 -translate-y-1/2 pointer-events-auto";
        wrapper.style.left = `${x}%`;
        wrapper.style.top = `${y}%`;
        wrapper.title = `${name}: ${value} ${unit}`;

        // circle badge with value; adjust size/classes as needed
        wrapper.innerHTML = `
            <div class="w-12 h-12 rounded-full bg-white bg-opacity-90 border border-gray-300 flex items-center justify-center text-sm font-semibold shadow">
                <div>
                    <div class="text-xs text-gray-600">${name}</div>
                    <div class="text-sm text-black">${value}${unit ? ' ' + unit : ''}</div>
                </div>
            </div>
        `;

        el.appendChild(wrapper);
    });
}

// Fetch sensors + recent data and update overlays
async function updateMainSensors() {
    try {
        const sensors = await fetchSensors();
        applySensorPositions(sensors);
        if (!sensors || !sensors.sensors || sensors.sensors.length === 0) {
            document.getElementById("top-overlay").innerText = "No sensors configured";
            document.getElementById("bottom-overlay").innerText = "No sensors configured";
            return;
        }

        // fetch recent data (use sinceseconds window)
        const sensorData = await fetchSensorData(Date.now() / 1000 - sinceseconds);
        const allData = sensorData.values;

        // split sensors by their configured y-position so top/bottom overlays are correct
        const list = sensors.sensors.map((s) => {
            // ensure x/y are numbers if present
            const x = typeof s.x === "number" ? s.x : null;
            const y = typeof s.y === "number" ? s.y : null;
            return Object.assign({}, s, { x, y });
        });

        const topSensors = list.filter((s) => (s.y !== null ? s.y < 50 : true)); // default to top if no pos
        const bottomSensors = list.filter((s) => (s.y !== null ? s.y >= 50 : false));

        renderOverlay("top-overlay", topSensors, allData);
        renderOverlay("bottom-overlay", bottomSensors, allData);
    } catch (err) {
        console.error("updateMainSensors error:", err);
    }
}

// Initialize main view updater (start periodic refresh)
function initializeMainView() {
    // clear any previous interval
    if (mainInterval) {
        clearInterval(mainInterval);
        mainInterval = null;
    }
    // initial render
    updateMainSensors();
    // refresh periodically
    mainInterval = setInterval(updateMainSensors, 1500);
}

// Stop main view updater when leaving main view
function stopMainView() {
    if (mainInterval) {
        clearInterval(mainInterval);
        mainInterval = null;
    }
}

// -----------------------------
// Init
// -----------------------------

document
    .getElementById("collector-btn")
    .addEventListener("click", handleCollectorRecord);

document.getElementById("replay-form").addEventListener("submit", handleReplay);

document.addEventListener("DOMContentLoaded", () => {
const params = new URLSearchParams(window.location.search);
    const view = params.get("view");
    const controlViewEl = document.getElementById("control-view");
    const mainViewEl = document.getElementById("main-view");

    const headerTitle = document.getElementById("header-title");
    if (headerTitle) {
        headerTitle.textContent = view === "control" ? "Control Panel" : "Water Dashboard";
    }
    if (view === "control") {
        controlViewEl?.classList.remove("hidden");
        initializeCharts();
        createValves();
        setInterval(update, 1500);
        // ensure main view updater is stopped
        stopMainView();
    } else {
        // ensure control view remains hidden for other views
        controlViewEl?.classList.add("hidden");
    }
    if (view === "main") {
        mainViewEl?.classList.remove("hidden");
        initializeMainView();
    } else {
        mainViewEl?.classList.add("hidden");
        stopMainView();
    }

});
