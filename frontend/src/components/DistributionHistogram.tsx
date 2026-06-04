import { useRef, useEffect } from "react";
import { useSimulationStore } from "../store/simulationStore";

export default function DistributionHistogram() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { snapshot } = useSimulationStore();
  const dist = snapshot?.distribution;

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
    const pad = { top: 30, right: 16, bottom: 30, left: 50 };

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, W, H);

    if (!dist?.bins || !dist?.counts || dist.bins.length < 2) {
      ctx.fillStyle = "#8b949e";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Waiting for data...", W / 2, H / 2);
      return;
    }

    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;
    const binCount = dist.counts.length;
    const maxCount = Math.max(...dist.counts, 1);

    // Bars
    const barWidth = plotW / binCount;
    dist.counts.forEach((count, i) => {
      const barH = (count / maxCount) * plotH;
      const x = pad.left + i * barWidth;
      const y = pad.top + plotH - barH;

      // Color gradient based on wealth level (darker = poorer, brighter = richer)
      const t = i / binCount;
      const r = Math.floor(80 + t * 100);
      const g = Math.floor(100 + t * 80);
      const b = Math.floor(180 - t * 60);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(x + 1, y, Math.max(barWidth - 2, 1), barH);
    });

    // Axes
    ctx.strokeStyle = "#30363d";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.stroke();

    // Labels
    ctx.fillStyle = "#8b949e";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Wealth (log scale)", W / 2, H - 4);
    ctx.save();
    ctx.translate(10, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("Agents", 0, 0);
    ctx.restore();

    // Title
    ctx.fillStyle = "#e1e4e8";
    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Wealth Distribution", pad.left, 18);
  }, [dist]);

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
    aspectRatio: "1.6",
    minHeight: 200,
  },
};
