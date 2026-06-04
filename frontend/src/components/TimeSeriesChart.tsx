import { useRef, useEffect } from "react";
import { useSimulationStore } from "../store/simulationStore";

const METRIC_COLORS: Record<string, string> = {
  gini: "#f78166",
  total_wealth: "#56d364",
  mean_wealth: "#58a6ff",
  median_wealth: "#d2a8ff",
  top_1_pct_share: "#f0883e",
  top_10_pct_share: "#e3b341",
  bottom_50_pct_share: "#7ee787",
  pareto_alpha: "#79c0ff",
};

const METRIC_NAMES: Record<string, string> = {
  gini: "基尼系数",
  top_1_pct_share: "Top 1%",
  top_10_pct_share: "Top 10%",
  bottom_50_pct_share: "底层 50%",
};

export default function TimeSeriesChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { history } = useSimulationStore();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = rect.height;
    const pad = { top: 24, right: 90, bottom: 28, left: 52 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, W, H);

    if (history.length < 2) {
      ctx.fillStyle = "#8b949e";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("收集数据中...", W / 2, H / 2);
      return;
    }

    const metrics = ["gini", "top_1_pct_share", "top_10_pct_share", "bottom_50_pct_share"];

    // 网格
    ctx.strokeStyle = "#21262d";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + (plotH * i) / 5;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
    }

    // 绘制每条指标线
    metrics.forEach((metric) => {
      const points: { x: number; y: number }[] = [];
      let minVal = Infinity;
      let maxVal = -Infinity;

      history.forEach((s, idx) => {
        const val = s.metrics?.[metric];
        if (val !== undefined && val !== null) {
          points.push({ x: idx, y: val });
          minVal = Math.min(minVal, val);
          maxVal = Math.max(maxVal, val);
        }
      });

      if (points.length < 2) return;

      const range = maxVal - minVal || 1;
      const totalTicks = history.length || 1;
      const color = METRIC_COLORS[metric] || "#8b949e";

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();
      points.forEach((p, i) => {
        const x = pad.left + (p.x / (totalTicks - 1)) * plotW;
        const y = pad.top + plotH - ((p.y - minVal) / range) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    });

    // 坐标轴
    ctx.strokeStyle = "#30363d";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.stroke();

    // X 轴标签
    ctx.fillStyle = "#8b949e";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("模拟步数 (tick)", W / 2, H - 6);

    // 图例
    ctx.textAlign = "left";
    metrics.forEach((m, i) => {
      const y = pad.top + 10 + i * 16;
      ctx.fillStyle = METRIC_COLORS[m] || "#8b949e";
      ctx.fillRect(pad.left + plotW + 8, y - 5, 10, 10);
      ctx.fillStyle = "#e1e4e8";
      ctx.font = "11px sans-serif";
      ctx.fillText(METRIC_NAMES[m] || m, pad.left + plotW + 22, y + 3);
    });

    // 标题
    ctx.fillStyle = "#e1e4e8";
    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("指标时序", pad.left, 16);
  }, [history]);

  return (
    <div style={styles.container}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: "#161b22",
    borderRadius: 8,
    padding: 0,
    border: "1px solid #30363d",
    overflow: "hidden",
    aspectRatio: "2.2",
    minHeight: 200,
  },
};
