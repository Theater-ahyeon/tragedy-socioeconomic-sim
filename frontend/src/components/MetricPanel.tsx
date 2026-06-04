import { useSimulationStore } from "../store/simulationStore";

export default function MetricPanel() {
  const { snapshot } = useSimulationStore();
  const metrics = snapshot?.metrics;

  const cards = [
    { label: "基尼系数", value: metrics?.gini, format: (v: number) => v.toFixed(4), color: "#f78166" },
    { label: "总财富", value: metrics?.total_wealth, format: (v: number) => `$${(v / 1000).toFixed(0)}k`, color: "#56d364" },
    { label: "平均财富", value: metrics?.mean_wealth, format: (v: number) => `$${v.toFixed(1)}`, color: "#58a6ff" },
    { label: "中位数财富", value: metrics?.median_wealth, format: (v: number) => `$${v.toFixed(1)}`, color: "#d2a8ff" },
    { label: "Top 1% 份额", value: metrics?.top_1_pct_share, format: (v: number) => `${(v * 100).toFixed(1)}%`, color: "#f0883e" },
    { label: "Top 10% 份额", value: metrics?.top_10_pct_share, format: (v: number) => `${(v * 100).toFixed(1)}%`, color: "#e3b341" },
    { label: "底层 50% 份额", value: metrics?.bottom_50_pct_share, format: (v: number) => `${(v * 100).toFixed(1)}%`, color: "#7ee787" },
    { label: "帕累托 α", value: metrics?.pareto_alpha, format: (v: number) => v.toFixed(2), color: "#79c0ff" },
    { label: "最大/最小比", value: metrics?.max_wealth && metrics?.min_wealth ? metrics.max_wealth / Math.max(metrics.min_wealth, 0.01) : undefined, format: (v: number) => `${v.toFixed(0)}x`, color: "#ff7b72" },
  ];

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>📊 经济指标</h2>
      <div style={styles.grid}>
        {cards.map((card) => (
          <div key={card.label} style={styles.card}>
            <span style={styles.cardLabel}>{card.label}</span>
            <span style={{ ...styles.cardValue, color: card.color }}>
              {card.value !== undefined && card.value !== null
                ? card.format(card.value)
                : "—"}
            </span>
          </div>
        ))}
      </div>
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
  title: {
    fontSize: 18,
    fontWeight: 600,
    color: "#e1e4e8",
    marginBottom: 12,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 8,
  },
  card: {
    background: "#0d1117",
    borderRadius: 6,
    padding: "10px 12px",
    border: "1px solid #21262d",
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  cardLabel: {
    fontSize: 11,
    color: "#8b949e",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  cardValue: {
    fontSize: 16,
    fontWeight: 700,
    fontFamily: "monospace",
  },
};
