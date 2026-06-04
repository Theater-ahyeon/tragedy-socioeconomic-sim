/** TypeScript types mirroring the Pydantic API schemas. */

export interface SimulationStatus {
  running: boolean;
  paused: boolean;
  tick: number;
  agent_count: number;
  tick_rate: number;
  model_name: string;
  uptime_seconds: number;
}

export interface SimulationSnapshot {
  type: "snapshot";
  tick: number;
  metrics: Record<string, number>;
  lorenz?: {
    population: number[];
    wealth: number[];
  };
  distribution?: {
    bins: number[];
    counts: number[];
  };
}

export interface SimulationEvent {
  type: "event";
  tick: number;
  event: string;
  data: Record<string, unknown>;
}

export type WSMessage = SimulationSnapshot | SimulationEvent;

export interface TimeSeriesData {
  ticks: number[];
  series: Record<string, (number | null)[]>;
}

export interface ConfigInfo {
  name: string;
  content: Record<string, unknown>;
}
