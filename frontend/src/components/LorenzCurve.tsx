import { useRef, useEffect } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function LorenzCurve() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { snapshot } = useSimulationStore();
  const lorenz = snapshot?.lorenz;
  const gini = snapshot?.metrics?.gini;

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
    const pad = 36;

    // 清空
    ctx.clearRect(0, 0, W, H);

    // 背景
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, W, H);

    // 网格
    ctx.strokeStyle = "#21262d";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const x = pad + ((W - 2 * pad) * i) / 5;
      const y = pad + ((H - 2 * pad) * i) / 5;
      ctx.beginPath();
      ctx.moveTo(x, pad);
      ctx.lineTo(x, H - pad);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(W - pad, y);
      ctx.stroke();
    }

    // 绝对平等线
    ctx.strokeStyle = "#30363d";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(pad, H - pad);
    ctx.lineTo(W - pad, pad);
    ctx.stroke();
    ctx.setLineDash([]);

    // 洛伦兹曲线
    if (lorenz?.population && lorenz?.wealth) {
      ctx.strokeStyle = "#58a6ff";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      for (let i = 0; i < lorenz.population.length; i++) {
        const x = pad + lorenz.population[i] * (W - 2 * pad);
        const y = H - pad - lorenz.wealth[i] * (H - 2 * pad);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // 曲线下方填充
      ctx.fillStyle = "rgba(88, 166, 255, 0.1)";
      ctx.lineTo(W - pad, H - pad);
      ctx.lineTo(pad, H - pad);
      ctx.closePath();
      ctx.fill();
    }

    // 坐标轴标签
    ctx.fillStyle = "#8b949e";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("人口累计 %", W / 2, H - 6);
    ctx.save();
    ctx.translate(10, H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("财富累计 %", 0, 0);
    ctx.restore();

    // 标题
    ctx.fillStyle = "#e1e4e8";
    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(
      `洛伦兹曲线${gini !== undefined ? ` — 基尼系数: ${gini.toFixed(4)}` : ""}`,
      pad,
      20
    );
  }, [lorenz, gini]);

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
    aspectRatio: "1",
    minHeight: 250,
  },
};
