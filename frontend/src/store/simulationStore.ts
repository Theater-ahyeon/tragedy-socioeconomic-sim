import { create } from "zustand";
import type { SimulationSnapshot, SimulationStatus } from "../types/api";

interface SimulationState {
  // Connection
  connected: boolean;

  // Status
  status: SimulationStatus | null;

  // Latest snapshot
  snapshot: SimulationSnapshot | null;

  // Time series history (for charts)
  history: SimulationSnapshot[];

  // Actions
  setConnected: (connected: boolean) => void;
  setStatus: (status: SimulationStatus) => void;
  addSnapshot: (snapshot: SimulationSnapshot) => void;
  clearHistory: () => void;
}

export const useSimulationStore = create<SimulationState>((set) => ({
  connected: false,
  status: null,
  snapshot: null,
  history: [],

  setConnected: (connected) => set({ connected }),

  setStatus: (status) => set({ status }),

  addSnapshot: (snapshot) =>
    set((state) => {
      const history = [...state.history, snapshot];
      // Keep last 5000 snapshots max
      if (history.length > 5000) {
        history.splice(0, history.length - 5000);
      }
      return { snapshot, history };
    }),

  clearHistory: () => set({ snapshot: null, history: [] }),
}));
