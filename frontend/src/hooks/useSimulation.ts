import { useState, useCallback, useEffect, useRef } from "react";
import type { SimulationStatus } from "../types/api";
import { useSimulationStore } from "../store/simulationStore";

const API_BASE = "http://localhost:8000/api/v1";

export function useSimulation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setStatus } = useSimulationStore();
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const apiCall = useCallback(async (path: string, method = "GET", body?: unknown) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const start = useCallback(
    async (configId: string, maxTicks?: number) => {
      return apiCall("/simulation/start", "POST", {
        config_id: configId,
        max_ticks: maxTicks ?? null,
        collect_every: 10,
      });
    },
    [apiCall]
  );

  const pause = useCallback(() => apiCall("/simulation/pause", "POST"), [apiCall]);
  const resume = useCallback(() => apiCall("/simulation/resume", "POST"), [apiCall]);
  const stop = useCallback(() => apiCall("/simulation/stop", "POST"), [apiCall]);
  const step = useCallback(() => apiCall("/simulation/step", "POST"), [apiCall]);

  const fetchStatus = useCallback(async () => {
    try {
      const status: SimulationStatus = await apiCall("/simulation/status");
      setStatus(status);
      return status;
    } catch {
      return null;
    }
  }, [apiCall, setStatus]);

  // Poll status every 2 seconds
  useEffect(() => {
    pollingRef.current = setInterval(fetchStatus, 2000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [fetchStatus]);

  return {
    start,
    pause,
    resume,
    stop,
    step,
    fetchStatus,
    loading,
    error,
  };
}
