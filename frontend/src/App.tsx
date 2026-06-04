import SimulationControl from "./components/SimulationControl";
import MetricPanel from "./components/MetricPanel";
import LorenzCurve from "./components/LorenzCurve";
import DistributionHistogram from "./components/DistributionHistogram";
import TimeSeriesChart from "./components/TimeSeriesChart";
import { useWebSocket } from "./hooks/useWebSocket";

export default function App() {
  useWebSocket();

  return (
    <div style={styles.layout}>
      {/* 左侧控制栏 */}
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <h1 style={styles.logoTitle}>🏛️ Tragedy</h1>
          <p style={styles.logoSub}>基于智能体的社会经济模拟</p>
        </div>
        <SimulationControl />
      </aside>

      {/* 主内容区 */}
      <main style={styles.main}>
        <MetricPanel />
        <TimeSeriesChart />
        <div style={styles.bottomRow}>
          <LorenzCurve />
          <DistributionHistogram />
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: "flex",
    width: "100vw",
    height: "100vh",
  },
  sidebar: {
    width: 280,
    minWidth: 280,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 16,
    borderRight: "1px solid #21262d",
    background: "#0d1117",
    overflowY: "auto",
  },
  logo: {
    marginBottom: 4,
  },
  logoTitle: {
    fontSize: 22,
    fontWeight: 800,
    color: "#e1e4e8",
    margin: 0,
  },
  logoSub: {
    fontSize: 12,
    color: "#8b949e",
    margin: 0,
    marginTop: 2,
  },
  main: {
    flex: 1,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 12,
    overflowY: "auto",
    background: "#0f1117",
  },
  bottomRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 12,
  },
};
