/* vitens-api.ts */

export interface Measurement {
    timestamp: number;
    value: number;
    unit: string;
}

export type MeasurementsByAlgorithm = Record<string, Measurement[]>;
export type MeasurementsBySensor = Record<string, MeasurementsByAlgorithm>;
export type MeasurementsByDevice = Record<string, MeasurementsBySensor>;

/* DB komt waarschijnlijk als ints terug (0/1). We modelleren conservatief als number. */
export interface ValveStatus {
    timestamp: number;
    state: 0 | 1;
    wants: 0 | 1;
}

export type ValvesByName = Record<string, ValveStatus>;
export type ValvesByDevice = Record<string, ValvesByName>;

export type ReplayActivePayload =
    | {
          device: string;
          active: false;
      }
    | {
          device: string;
          active: true;
          timestamp: number;
          progress: number;
      };

export type CollectorActivePayload =
    | {
          device: string;
          active: false;
      }
    | {
          device: string;
          active: true;
          dbname: string;
          timeleft: number;
          progress: number;
      };

export type CollectorStatusResponse = Record<string, CollectorActivePayload>;
export type ReplayStatusResponse = Record<string, ReplayActivePayload>;

export interface OkResponse {
    error: null;
}

export interface ApiErrorResponse {
    error: string;
}

/* Requests */
export interface SetValveStateRequest {
    device: string;
    valve: string;
    state: 0 | 1;
}

/* Error type met status + body voor debug */
export class VitensAPIError extends Error {
    public readonly status: number | null;
    public readonly payload: unknown;

    constructor(message: string, status: number | null, payload: unknown) {
        super(message);
        this.name = "VitensAPIError";
        this.status = status;
        this.payload = payload;
    }
}

function isObject(v: unknown): v is Record<string, unknown> {
    return typeof v === "object" && v !== null;
}

function hasErrorField(v: unknown): v is ApiErrorResponse | OkResponse {
    return isObject(v) && "error" in v;
}

export class VitensAPI {
    constructor(public readonly host = "") {}

    private buildUrl(path: string): string {
        return this.host ? this.host.replace(/\/+$/, "") + path : path;
    }

    private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
        const url = this.buildUrl(path);

        const resp = await fetch(url, init);

        // Niet elke response is gegarandeerd JSON, maar jouw server is dat wel.
        // Toch defensief:
        let payload: unknown;
        const text = await resp.text();
        try {
            payload = text.length ? JSON.parse(text) : null;
        } catch {
            payload = text;
        }

        // 1) Flask-style {error: "..."} error
        if (hasErrorField(payload) && payload.error) {
            throw new VitensAPIError(
                String(payload.error),
                resp.status ?? null,
                payload
            );
        }

        // 2) HTTP error zonder {error: "..."} (als je dat ooit gaat toevoegen)
        if (!resp.ok) {
            throw new VitensAPIError(
                `HTTP ${resp.status} ${resp.statusText}`,
                resp.status ?? null,
                payload
            );
        }

        return payload as T;
    }

    private async get<T>(path: string): Promise<T> {
        return this.request<T>(path, { method: "GET" });
    }

    private async post<T>(path: string, body?: unknown): Promise<T> {
        return this.request<T>(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body ?? {}),
        });
    }

    /* ========= endpoints (matchen je Flask routes) ========= */

    /** GET /api/sensors?since=... */
    fetchSensorData(since: number): Promise<MeasurementsByDevice> {
        return this.get<MeasurementsByDevice>(`/api/sensors?since=${since}`);
    }

    /** GET /api/valves */
    fetchValves(): Promise<ValvesByDevice> {
        return this.get<ValvesByDevice>(`/api/valves`);
    }

    /** POST /api/valves */
    setValveState(
        device: string,
        valve: string,
        state: 0 | 1
    ): Promise<OkResponse> {
        return this.post<OkResponse>(`/api/valves`, { device, valve, state });
    }

    /** GET /api/collector */
    fetchCollector(): Promise<CollectorStatusResponse> {
        return this.get<CollectorStatusResponse>(`/api/collector`);
    }

    /** POST /api/collector */
    startCollector(device: string): Promise<OkResponse> {
        return this.post<OkResponse>(`/api/collector`, { device });
    }

    /** POST /api/collector/stop */
    stopCollector(device: string): Promise<OkResponse> {
        return this.post<OkResponse>(`/api/collector/stop`, { device });
    }

    /** GET /api/replay */
    fetchReplay(): Promise<ReplayStatusResponse> {
        return this.get<ReplayStatusResponse>(`/api/replay`);
    }

    /** POST /api/replay */
    startReplay(device: string, timestamp: number): Promise<OkResponse> {
        return this.post<OkResponse>(`/api/replay`, { device, timestamp });
    }

    /** POST /api/replay/stop */
    stopReplay(device: string): Promise<OkResponse> {
        return this.post<OkResponse>(`/api/replay/stop`, { device });
    }
}
