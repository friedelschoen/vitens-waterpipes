import { Chart, registerables } from "chart.js";
import {
    CollectorActivePayload,
    MeasurementsByAlgorithm,
    ReplayActivePayload,
    VitensAPI,
} from "./api";

Chart.register(...registerables);

const api = new VitensAPI();
const sinceseconds = 60; // = 2 minute; Max number of data points retained per chart

let lastTimestamp = 0; // Track newest timestamp to fetch/update correctly

class Sensor {
    public latestDataEl: HTMLElement;
    public chart: Chart<"line", { x: number; y: number }[]>;
    public algorithms: string[];

    constructor(
        parent: Device,
        public sensorKey: string,
        sensorData: MeasurementsByAlgorithm
    ) {
        const card = document.createElement("div");
        card.style.marginBottom = "40px";

        const latestId = `latest-data-${sensorKey}-${parent.name}`;
        const canvasId = `lineChart${sensorKey}-${parent.name}`;

        card.innerHTML = `
            <h2 style="text-align:center; font-weight:bold; margin-bottom: 10px;">
                ${sensorKey}
            </h2>
            <h3 style="text-align:center; margin-bottom: 10px;"><span id="${latestId}">N/A</span> ${
            sensorData.none[0].unit ?? ""
        }</h3>
            <canvas id="${canvasId}"></canvas>
        `;

        parent.chartsContainer.appendChild(card);

        const ctx = (<HTMLCanvasElement>(
            document.getElementById(canvasId)
        )).getContext("2d");

        let datasets = Object.entries(sensorData).map(([algo, algodata]) => ({
            label:
                algo == "none"
                    ? `${sensorKey} (Actual)`
                    : `${algo} (Predicted)`,
            data: algodata.map((row) => ({
                x: row.timestamp,
                y: row.value,
            })),
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0,
        }));

        this.chart = new Chart(ctx, {
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
                            callback(value: number) {
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
                        suggestedMax: 3,
                    },
                },
            },
        });

        this.algorithms = Object.keys(sensorData);

        const latestValue = sensorData.none[sensorData.none.length - 1];

        this.latestDataEl = document.getElementById(latestId);
        this.latestDataEl.textContent = `Latest Data (const): ${
            latestValue?.value?.toFixed(2) ?? "N/A"
        }`;
    }

    clear() {
        this.chart.destroy();
    }
}

class Valve {
    public div: HTMLElement;
    public stateSpan: HTMLElement;
    public openBtn: HTMLButtonElement;
    public closeBtn: HTMLButtonElement;

    constructor(public parent: Device, public name: string) {
        const wrapper = document.createElement("div");
        wrapper.id = `valve-${name}-${parent.name}`;
        wrapper.className =
            "bg-white rounded-xl mt-4 p-6 w-72 shadow-md flex flex-col items-center";
        wrapper.innerHTML = `
            <h2 class="text-xl font-semibold mb-2 text-gray-800">${name}</h2>
            <p id="valve-state-${name}-${parent.name}" class="mb-4 text-gray-500">
                Valve is now
                <span class="font-semibold text-red-400">closed</span>
            </p>
            <div class="flex gap-4">
                <button
                    class="bg-neutral-700 hover:bg-neutral-800 text-white font-medium py-2 px-5 rounded transition"
                    data-action="1"
                    id="open-btn-${name}-${parent.name}">
                    Open
                </button>
                <button
                    class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-5 rounded transition"
                    data-action="0"
                    id="close-btn-${name}-${parent.name}">
                    Close
                </button>
            </div>
        `;

        parent.valvesDiv.appendChild(wrapper);

        // Event listeners
        this.div = document.getElementById(`valve-${name}-${parent.name}`);
        this.stateSpan = document.getElementById(
            `valve-state-${name}-${parent.name}`
        );
        this.openBtn = <HTMLButtonElement>(
            document.getElementById(`open-btn-${name}-${parent.name}`)
        );
        this.closeBtn = <HTMLButtonElement>(
            document.getElementById(`close-btn-${name}-${parent.name}`)
        );

        this.openBtn.addEventListener("click", (ev) =>
            this.handleValveButtonClick(ev)
        );
        this.closeBtn.addEventListener("click", (ev) =>
            this.handleValveButtonClick(ev)
        );
    }

    handleValveButtonClick(e: MouseEvent) {
        const target = e.currentTarget as HTMLButtonElement;
        const actionText = target.getAttribute("data-action");
        const action = parseInt(actionText) as 0 | 1;

        console.log(`${this.parent.name}->${this.name} = ${action}`);
        api.setValveState(this.parent.name, this.name, action)
            .then(() => this.update(action, action))
            .catch(console.error);
    }

    update(open: 0 | 1, wantsOpen: 0 | 1) {
        if (open !== wantsOpen) {
            this.div.classList.add("bg-red-100");
            this.div.classList.remove("bg-white");
        } else {
            this.div.classList.add("bg-white");
            this.div.classList.remove("bg-red-100");
        }

        this.stateSpan.classList.remove(
            "text-green-500",
            "text-red-400",
            "text-black",
            "font-bold",
            "font-semibold"
        );

        if (open) {
            this.stateSpan.innerHTML = `Valve is now <span class="text-green-500">open</span>`;
            if (!wantsOpen) {
                this.stateSpan.innerHTML += `<b>, but wants <span class="text-red-400">closed</span></b>`;
            }
        } else {
            this.stateSpan.innerHTML = `Valve is now <span class="text-red-400">closed</span>`;
            if (wantsOpen) {
                this.stateSpan.innerHTML += `<b>, but wants <span class="text-green-400">open</span></b>`;
            }
        }

        // this.openBtn.disabled = false;
        // this.closeBtn.disabled = false;

        this.openBtn.classList.remove(
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
        this.closeBtn.classList.remove(
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
            this.openBtn.classList.add(
                "bg-green-500",
                "text-white",
                "font-bold",
                "ring",
                "ring-green-300"
            );
            if (!open) {
                this.openBtn.classList.add("animate-pulse");
            }
            this.closeBtn.classList.add(
                "bg-gray-300",
                "hover:bg-gray-400",
                "text-gray-800"
            );
        } else {
            this.closeBtn.classList.add(
                "bg-red-500",
                "text-white",
                "font-bold",
                "ring",
                "ring-red-300"
            );
            if (open) {
                this.closeBtn.classList.add("animate-pulse");
            }
            this.openBtn.classList.add(
                "bg-gray-300",
                "hover:bg-gray-400",
                "text-gray-800"
            );
        }
    }
}

class Device {
    public collectorDbname: HTMLElement;
    public collectorState: HTMLElement;
    public collectorProgress: HTMLElement;
    public collectorBtn: HTMLButtonElement;
    public replayState: HTMLElement;
    public replayProgress: HTMLElement;
    public replayForm: HTMLElement;
    public replayTime: HTMLInputElement;
    public replayBtn: HTMLButtonElement;
    public valvesDiv: HTMLElement;
    public flowSection: HTMLElement;
    public chartsContainer: HTMLElement;

    public sensors: Record<string, Sensor> = {};
    public valves: Record<string, Valve> = {};

    protected collectorActive = false;
    protected replayActive = false;

    constructor(public name: string, mainDiv: HTMLElement) {
        if (mainDiv.childNodes.length > 0) {
            let line = document.createElement("hr");
            line.classList.add("border-gray-400");
            mainDiv.appendChild(line);
        }
        let devSection = document.createElement("main");
        devSection.classList.add("flex-1", "flex", "flex-col", "text-center");
        devSection.innerHTML += `
        <h1 class="text-2xl m-10 font-bold font-mono">${name}</h1>
        <section class="py-6 sm:px-12 flex justify-center">
            <div class="bg-white rounded-xl mt-4 p-6 w-1/3 shadow-md flex flex-col items-center justify-center m-6">
                <h2 class="text-xl font-semibold mb-2 text-gray-800">Collector<code id="${name}-collector-dbname"></code></h2>
                <p class="mb-2 text-gray-500">
                    Collector is currently
                    <span id="${name}-collector-state" class="font-semibold text-red-400 ">inactive</span>
                </p>
                <p id="${name}-collector-progress" class="hidden text-center mb-2 text-gray-500">
                </p>
                <div class=" flex gap-4">
                    <button id="${name}-collector-btn"
                        class="hover:bg-gray-400 font-medium py-2 px-5 rounded transition bg-red-500 text-white font-bold">
                        Record
                    </button>
                </div>
            </div>

            <div class="bg-white rounded-xl mt-4 p-6 w-1/3 shadow-md flex flex-col items-center justify-center m-6">
                <h2 class="text-xl font-semibold mb-2 text-gray-800">Replay</h2>
                <p class="mb-2 text-gray-500">
                    Replay is currently
                    <span id="${name}-replay-state" class="font-semibold text-gray-700 ">inactive</span>
                </p>
                <p id="${name}-replay-progress" class="hidden text-center mb-2 text-gray-500">
                </p>
                <div class=" flex gap-4">
                    <form id="${name}-replay-form">
                        <input type="datetime-local" step="1" id="${name}-replay-time"
                            class="font-medium py-2 px-5 rounded transition bg-gray-100" />
                        <input type="submit" id="${name}-replay-btn"
                            class="hover:bg-gray-400 font-medium py-2 px-5 rounded transition bg-yellow-500 text-white font-bold"
                            value="Replay" />
                    </form>
                </div>
            </div>
        </section>

        <section class="py-6 px-6 sm:px-12">
            <div id="${name}-valves-div" class="flex flex-wrap justify-center gap-8">
            </div>
        </section>

        <section class="w-full p-8">
            <div id="${name}-chartsContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        </section>
    `;

        mainDiv.appendChild(devSection);
        this.collectorDbname = document.getElementById(
            `${name}-collector-dbname`
        );
        this.collectorState = document.getElementById(
            `${name}-collector-state`
        );
        this.collectorProgress = document.getElementById(
            `${name}-collector-progress`
        );
        this.collectorBtn = <HTMLButtonElement>(
            document.getElementById(`${name}-collector-btn`)
        );
        this.replayState = document.getElementById(`${name}-replay-state`);
        this.replayProgress = document.getElementById(
            `${name}-replay-progress`
        );
        this.replayForm = document.getElementById(`${name}-replay-form`);
        this.replayTime = <HTMLInputElement>(
            document.getElementById(`${name}-replay-time`)
        );
        this.replayBtn = <HTMLButtonElement>(
            document.getElementById(`${name}-replay-btn`)
        );
        this.valvesDiv = document.getElementById(`${name}-valves-div`);
        this.chartsContainer = document.getElementById(
            `${name}-chartsContainer`
        );

        this.collectorBtn.addEventListener("click", async () => {
            if (!this.collectorActive) {
                await api.startCollector(this.name);
                this.activateCollector();
            } else {
                await api.stopCollector(this.name);
                this.deactivateCollector();
            }
        });

        this.replayForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            if (!this.replayActive) {
                const timestamp = Date.parse(this.replayTime.value);
                await api.startReplay(this.name, timestamp);
                this.activateReplay();
            } else {
                await api.stopReplay(this.name);
                this.deactivateReplay();
            }
        });
    }

    activateCollector() {
        if (this.collectorActive) return;
        this.collectorActive = true;
        this.collectorBtn.innerText = "Cancel";
        this.collectorBtn.classList.add("bg-gray-800");
        this.collectorBtn.classList.remove("bg-red-500");

        this.collectorState.innerHTML = "active";
        this.collectorState.classList.add("text-green-300");
        this.collectorState.classList.remove("text-gray-700");
    }

    deactivateCollector() {
        if (!this.collectorActive) return;
        this.collectorActive = false;

        this.collectorBtn.innerText = "Record";
        this.collectorBtn.classList.add("bg-red-500");
        this.collectorBtn.classList.remove("bg-gray-800");

        this.collectorState.innerHTML = "inactive";
        this.collectorState.classList.add("text-gray-700");
        this.collectorState.classList.remove("text-green-300");

        this.collectorProgress.classList.add("hidden");
        this.collectorDbname.innerText = "";
    }

    updateCollector(collector: CollectorActivePayload) {
        if (collector.active) {
            this.activateCollector();

            const percent = Math.floor(collector.progress * 100);
            const min = Math.round(collector.timeleft / 60);
            const sec = Math.round(collector.timeleft) % 60;
            const secstr = sec.toString().padStart(2, "0");
            this.collectorProgress.classList.remove("hidden");
            this.collectorProgress.innerHTML = `${percent}% &mdash; ${min}:${secstr} left`;

            this.collectorDbname.innerText = " " + collector.dbname;
        } else {
            this.deactivateCollector();
        }
    }

    activateReplay() {
        if (this.replayActive) return;
        this.replayActive = true;

        this.replayBtn.value = "Stop";
        this.replayBtn.classList.add("bg-gray-800");
        this.replayBtn.classList.remove("bg-yellow-500");

        this.replayState.innerHTML = "active";
        this.replayState.classList.add("text-yellow-300");
        this.replayState.classList.remove("text-gray-700");
    }

    deactivateReplay() {
        if (!this.replayActive) return;
        this.replayActive = false;

        this.replayBtn.value = "Replay";
        this.replayBtn.classList.add("bg-yellow-500");
        this.replayBtn.classList.remove("bg-gray-800");

        this.replayState.innerHTML = "inactive";
        this.replayState.classList.add("text-yellow-400");
        this.replayState.classList.remove("text-gray-700");

        this.replayProgress.classList.add("hidden");
    }

    updateReplay(replay: ReplayActivePayload) {
        if (replay.active) {
            this.activateReplay();

            const timestr = new Date(
                replay.timestamp * 1000
            ).toLocaleTimeString([], {
                day: "2-digit",
                month: "2-digit",
                year: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: false,
            });
            const percent = (replay.progress * 100).toFixed(1);

            this.replayProgress.classList.remove("hidden");
            this.replayProgress.innerHTML = `${percent}% &mdash; replaying at ${timestr}`;
        } else {
            this.deactivateReplay();
        }
    }
}

let devices: Record<string, Device> = {};

/**
 * Haal nieuwe data op en schuif de bestaande charts door
 */
async function update() {
    const data = await api.fetchSensorData(lastTimestamp);
    const mainDiv = document.getElementById("main");

    let newTimestamp = lastTimestamp;
    for (let [devName, deviceData] of Object.entries(data)) {
        if (!(devName in devices)) {
            devices[devName] = new Device(devName, mainDiv);
        }
        let dev = devices[devName];

        for (let [sensorName, sensorData] of Object.entries(deviceData)) {
            if (!sensorName.includes(".")) continue;
            if (!(sensorName in dev.sensors)) {
                dev.sensors[sensorName] = new Sensor(
                    dev,
                    sensorName,
                    sensorData
                );
            } else {
                let chart = dev.sensors[sensorName];
                for (let predname of chart.algorithms) {
                    let index = chart.algorithms.indexOf(predname);
                    let set = chart.chart.data.datasets[index];
                    for (let row of sensorData[predname]) {
                        if (row.timestamp <= lastTimestamp) continue;

                        if (row.timestamp > newTimestamp)
                            newTimestamp = row.timestamp;

                        set.data.push({
                            x: row.timestamp,
                            y: row.value,
                        });
                    }

                    let since = Date.now() / 1000 - sinceseconds;
                    while (set.data.length > 0 && set.data[0].x < since) {
                        set.data.shift();
                    }
                }
                chart.chart.update();
                chart.latestDataEl.innerText = `Latest Data: ${
                    sensorData.none[sensorData.none.length - 1].value.toFixed(
                        2
                    ) ?? "N/A"
                }`;
            }
        }
    }
    lastTimestamp = newTimestamp;

    const valves = await api.fetchValves();
    for (let [devName, deviceData] of Object.entries(valves)) {
        if (!(devName in devices)) {
            continue;
        }
        let dev = devices[devName];

        for (let [valveName, valveData] of Object.entries(deviceData)) {
            if (!(valveName in dev.valves)) {
                dev.valves[valveName] = new Valve(dev, valveName);
            } else {
                dev.valves[valveName].update(valveData.state, valveData.wants);
            }
        }
    }

    const collector = await api.fetchCollector();
    for (let [devName, col] of Object.entries(collector)) {
        if (!(devName in devices)) {
            continue;
        }
        devices[devName].updateCollector(col);
    }

    const replay = await api.fetchReplay();
    for (let [devName, repl] of Object.entries(replay)) {
        if (!("replay!" + devName in devices)) {
            continue;
        }
        devices["replay!" + devName].updateReplay(repl);
    }
}

// ADDED: persistent overlays map and shared positions
const positions: {
    top: Record<string, { left: number; top: number }>;
    bottom: Record<string, { left: number; top: number }>;
} = {
    top: {
        // flows
        flow0: { left: 20, top: 5 },
        flow1: { left: 10, top: 52 },
        // pressures
        pressure0: { left: 10, top: 25 },
        pressure1: { left: 85, top: 82 },
        // valves (named valve0 / valve1)
        valve0: { left: 30, top: 30 },
        valve1: { left: 40, top: 82 },
    },
    bottom: {
        // flows
        flow2: { left: 80, top: 35 },
        flow3: { left: 50, top: 62 },
        flow4: { left: 80, top: 44 },
        // pressures
        pressure2: { left: 15, top: 50 },
        pressure3: { left: 40, top: 72 },
        pressure4: { left: 65, top: 72 },
        pressure5: { left: 85, top: 60 },
        // valves (named valve2 / valve3 / valve4)
        valve2: { left: 30, top: 22 },
        valve3: { left: 60, top: 32 },
        valve4: { left: 80, top: 52 },
    },
};

const layerOverlays: Record<string, HTMLElement> = {}; // key -> element

async function updateLayers() {
    const topWrapper = document.getElementById("top-wrapper");
    const bottomWrapper = document.getElementById("bottom-wrapper");
    if (!topWrapper || !bottomWrapper) return;

    // fetch latest sensor data and valves
    const data = await api.fetchSensorData(0);
    const valves = await api.fetchValves();

    // helper to update overlay safely
    function setOverlay(key: string, html: string) {
        const el = layerOverlays[key];
        if (!el) return;
        el.innerHTML = html;
    }

    // Update sensor overlays: for each configured key find first matching sensor across devices
    for (const [key, pos] of Object.entries(positions.top)) {
        if (!key.startsWith("flow") && !key.startsWith("pressure")) continue;
        let found = false;
        for (const [devName, deviceData] of Object.entries(data)) {
            for (const [sensorName, sensorData] of Object.entries(deviceData)) {
                if (!sensorName.includes(".")) continue;
                if (sensorName.toLowerCase().includes(key)) {
                    const latest =
                        sensorData.none?.[sensorData.none.length - 1];
                    const valueStr = latest ? latest.value.toFixed(2) : "N/A";
                    setOverlay(
                        `top:${key}`,
                        `<span class="label">${devName} · ${key}</span><span class="value">${valueStr}</span>`
                    );
                    found = true;
                    break;
                }
            }
            if (found) break;
        }
        if (!found)
            setOverlay(
                `top:${key}`,
                `<span class="label">${key}</span><span class="value">N/A</span>`
            );
    }

    for (const [key, pos] of Object.entries(positions.bottom)) {
        if (!key.startsWith("flow") && !key.startsWith("pressure")) continue;
        let found = false;
        for (const [devName, deviceData] of Object.entries(data)) {
            for (const [sensorName, sensorData] of Object.entries(deviceData)) {
                if (!sensorName.includes(".")) continue;
                if (sensorName.toLowerCase().includes(key)) {
                    const latest =
                        sensorData.none?.[sensorData.none.length - 1];
                    const valueStr = latest ? latest.value.toFixed(2) : "N/A";
                    setOverlay(
                        `bottom:${key}`,
                        `<span class="label">${devName} · ${key}</span><span class="value">${valueStr}</span>`
                    );
                    found = true;
                    break;
                }
            }
            if (found) break;
        }
        if (!found)
            setOverlay(
                `bottom:${key}`,
                `<span class="label">${key}</span><span class="value">N/A</span>`
            );
    }

    // Update valve overlays (skip bigvalve*)
    // For each configured valve key look for matching valve across devices
    for (const key of Object.keys(positions.top)) {
        if (!key.startsWith("valve")) continue;
        let found = false;
        for (const [devName, deviceValves] of Object.entries(valves)) {
            for (const [valveName, valveData] of Object.entries(deviceValves)) {
                if (valveName.toLowerCase().includes("bigvalve")) continue;
                if (valveName.toLowerCase().includes(key)) {
                    const stateHtml = valveData.state
                        ? `<span class="valve-open">open</span>`
                        : `<span class="valve-closed">closed</span>`;
                    setOverlay(
                        `top:${key}`,
                        `<span class="label">${devName} · ${valveName}</span><span class="value">${stateHtml}</span>`
                    );
                    found = true;
                    break;
                }
            }
            if (found) break;
        }
        if (!found)
            setOverlay(
                `top:${key}`,
                `<span class="label">${key}</span><span class="value">N/A</span>`
            );
    }

    for (const key of Object.keys(positions.bottom)) {
        if (!key.startsWith("valve")) continue;
        let found = false;
        for (const [devName, deviceValves] of Object.entries(valves)) {
            for (const [valveName, valveData] of Object.entries(deviceValves)) {
                if (valveName.toLowerCase().includes("bigvalve")) continue;
                if (valveName.toLowerCase().includes(key)) {
                    const stateHtml = valveData.state
                        ? `<span class="valve-open">open</span>`
                        : `<span class="valve-closed">closed</span>`;
                    setOverlay(
                        `bottom:${key}`,
                        `<span class="label">${devName} · ${valveName}</span><span class="value">${stateHtml}</span>`
                    );
                    found = true;
                    break;
                }
            }
            if (found) break;
        }
        if (!found)
            setOverlay(
                `bottom:${key}`,
                `<span class="label">${key}</span><span class="value">N/A</span>`
            );
    }
}

function initLayersPage() {
    const topWrapper = document.getElementById("top-wrapper");
    const bottomWrapper = document.getElementById("bottom-wrapper");
    if (!topWrapper || !bottomWrapper) return;

    // Create overlays once (do not remove on update)
    function createOverlay(
        container: HTMLElement,
        scope: "top" | "bottom",
        key: string,
        pos: { left: number; top: number }
    ) {
        const id = `${scope}:${key}`;
        if (layerOverlays[id]) return;
        const el = document.createElement("div");
        el.className = "overlay";
        el.id = `overlay-${scope}-${key}`;
        el.style.left = pos.left + "%";
        el.style.top = pos.top + "%";
        el.innerHTML = `<span class="label">${key}</span><span class="value">...</span>`;
        container.appendChild(el);
        layerOverlays[id] = el;
    }

    // create for top keys
    for (const [k, p] of Object.entries(positions.top)) {
        createOverlay(topWrapper, "top", k, p);
    }
    // create for bottom keys
    for (const [k, p] of Object.entries(positions.bottom)) {
        createOverlay(bottomWrapper, "bottom", k, p);
    }

    // initial populate and poll (will update innerHTML only)
    updateLayers();
    setInterval(updateLayers, 2000);
}

document.addEventListener("DOMContentLoaded", () => {
    // update();
    // setInterval(update, 2000);

    if (
        document.getElementById("top-wrapper") &&
        document.getElementById("bottom-wrapper")
    ) {
        initLayersPage();
    }
});
