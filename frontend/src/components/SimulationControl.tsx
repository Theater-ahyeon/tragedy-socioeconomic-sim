import { useSimulationStore } from "../store/simulationStore";
import { useSimulation } from "../hooks/useSimulation";
import { useWebSocket } from "../hooks/useWebSocket";

export default function SimulationControl() {
  const { status, connected } = useSimulationStore();
  const { start, pause, resume, stop, loading, error } = useSimulation();
  const { sendCommand } = useWebSocket();

  const isRunning = status?.running && !status?.paused;
  const isPaused = status?.paused;
  const hasStatus = status !== null;

  const handleStart = () => start("yard_sale", 10000);
  // 已连接时用 WebSocket 命令（低延迟），否则 HTTP fallback
  const handlePause = () => connected ? sendCommand("pause") : pause();
  const handleResume = () => connected ? sendCommand("resume") : resume();
  const handleStop = () => connected ? sendCommand("stop") : stop();

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>⚙️ 控制面板</h2>
        <span style={{
          ...styles.status,
          background: connected ? "#238636" : hasStatus ? "#9e6a03" : "#da3633",
        }}>
          {connected ? "已连接" : hasStatus ? "实时断开" : "未连接"}
        </span>
      </div>

      <div style={styles.buttons}>
        <button
          onClick={handleStart}
          disabled={isRunning || loading}
          style={{
            ...styles.btn,
            ...(isRunning || loading ? styles.btnDisabled : styles.btnStart),
          }}
        >
          ▶ 启动
        </button>
        <button
          onClick={handlePause}
          disabled={!isRunning}
          style={{
            ...styles.btn,
            ...(!isRunning ? styles.btnDisabled : styles.btnPause),
          }}
        >
          ⏸ 暂停
        </button>
        <button
          onClick={handleResume}
          disabled={!isPaused}
          style={{
            ...styles.btn,
            ...(!isPaused ? styles.btnDisabled : styles.btnResume),
          }}
        >
          ▶ 继续
        </button>
        <button
          onClick={handleStop}
          disabled={!status?.running}
          style={{
            ...styles.btn,
            ...(!status?.running ? styles.btnDisabled : styles.btnStop),
          }}
        >
          ⏹ 停止
        </button>
      </div>

      {error && (
        <div style={styles.error}>
          ⚠️ {error}
        </div>
      )}

      {status && (
        <div style={styles.info}>
          <InfoRow label="当前步数" value={status.tick.toLocaleString()} />
          <InfoRow label="智能体数" value={status.agent_count.toLocaleString()} />
          <InfoRow label="速度" value={`${status.tick_rate.toFixed(0)} t/s`} />
          <InfoRow label="模型" value={status.model_name || "yard_sale"} />
          <InfoRow label="运行时间" value={`${status.uptime_seconds.toFixed(0)}s`} />
        </div>
      )}

      {!status?.running && !loading && (
        <p style={styles.hint}>点击 ▶ 启动 开始模拟</p>
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
    transition: "opacity 0.2s",
  },
  btnDisabled: {
    opacity: 0.4,
    cursor: "not-allowed",
  },
  btnStart: { background: "#238636", borderColor: "#238636", color: "#fff" },
  btnPause: { background: "#9e6a03", borderColor: "#9e6a03", color: "#fff" },
  btnResume: { background: "#1f6feb", borderColor: "#1f6feb", color: "#fff" },
  btnStop: { background: "#da3633", borderColor: "#da3633", color: "#fff" },
  error: {
    background: "#490202",
    border: "1px solid #da3633",
    borderRadius: 6,
    padding: "8px 12px",
    marginBottom: 12,
    color: "#f85149",
    fontSize: 13,
  },
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
