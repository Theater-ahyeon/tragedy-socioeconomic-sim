import { useSimulationStore } from "../store/simulationStore";
import { useSimulation } from "../hooks/useSimulation";
import { useWebSocket } from "../hooks/useWebSocket";

export default function SimulationControl() {
  const { status, connected } = useSimulationStore();
  const { start, pause, resume, stop, loading } = useSimulation();
  const { sendCommand } = useWebSocket();

  const isRunning = status?.running && !status?.paused;
  const isPaused = status?.paused;

  const handleStart = () => start("yard_sale", 10000);
  const handlePause = () => { pause(); sendCommand("pause"); };
  const handleResume = () => { resume(); sendCommand("resume"); };
  const handleStop = () => { stop(); sendCommand("stop"); };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>⚙️ Control</h2>
        <span style={{
          ...styles.status,
          background: connected ? "#238636" : "#da3633",
        }}>
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      <div style={styles.buttons}>
        <button
          onClick={handleStart}
          disabled={isRunning || loading}
          style={{ ...styles.btn, ...styles.btnStart }}
        >
          ▶ Start
        </button>
        <button
          onClick={handlePause}
          disabled={!isRunning}
          style={{ ...styles.btn, ...styles.btnPause }}
        >
          ⏸ Pause
        </button>
        <button
          onClick={handleResume}
          disabled={!isPaused}
          style={{ ...styles.btn, ...styles.btnResume }}
        >
          ▶ Resume
        </button>
        <button
          onClick={handleStop}
          disabled={!status?.running}
          style={{ ...styles.btn, ...styles.btnStop }}
        >
          ⏹ Stop
        </button>
      </div>

      {status && (
        <div style={styles.info}>
          <InfoRow label="Tick" value={status.tick.toLocaleString()} />
          <InfoRow label="Agents" value={status.agent_count.toLocaleString()} />
          <InfoRow label="Speed" value={`${status.tick_rate.toFixed(0)} t/s`} />
          <InfoRow label="Model" value={status.model_name || "yard_sale"} />
        </div>
      )}

      {!status?.running && !loading && (
        <p style={styles.hint}>Press ▶ Start to begin simulation</p>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.row}>
      <span style={styles.label}>{label}</span>
      <span style={styles.value}>{value}</span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: "#161b22",
    borderRadius: 8,
    padding: 16,
    border: "1px solid #30363d",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: 600,
    color: "#e1e4e8",
  },
  status: {
    padding: "4px 8px",
    borderRadius: 12,
    fontSize: 12,
    color: "#fff",
    fontWeight: 600,
  },
  buttons: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 8,
    marginBottom: 16,
  },
  btn: {
    padding: "10px 16px",
    border: "1px solid #30363d",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 600,
    color: "#c9d1d9",
    background: "#21262d",
  },
  btnStart: { background: "#238636", borderColor: "#238636", color: "#fff" },
  btnPause: { background: "#9e6a03", borderColor: "#9e6a03", color: "#fff" },
  btnResume: { background: "#1f6feb", borderColor: "#1f6feb", color: "#fff" },
  btnStop: { background: "#da3633", borderColor: "#da3633", color: "#fff" },
  info: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  row: {
    display: "flex",
    justifyContent: "space-between",
  },
  label: {
    color: "#8b949e",
    fontSize: 13,
  },
  value: {
    color: "#e1e4e8",
    fontSize: 13,
    fontWeight: 600,
    fontFamily: "monospace",
  },
  hint: {
    color: "#8b949e",
    fontSize: 13,
    textAlign: "center",
    marginTop: 12,
  },
};
