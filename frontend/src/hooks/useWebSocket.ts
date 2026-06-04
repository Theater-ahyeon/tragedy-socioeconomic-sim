import { useEffect, useRef, useCallback } from "react";
import { useSimulationStore } from "../store/simulationStore";
import type { WSMessage } from "../types/api";

// 使用相对路径 WebSocket，由 Vite 代理转发
const WS_URL = `ws://${window.location.host}/ws/simulation`;
const RECONNECT_DELAY = 2000;

export function useWebSocket() {
  const { setConnected, addSnapshot, clearHistory } = useSimulationStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      clearHistory();
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        if (message.type === "snapshot") {
          addSnapshot(message);
        }
      } catch {
        // 忽略解析错误
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // 自动重连
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [setConnected, addSnapshot, clearHistory]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, [setConnected]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const sendCommand = useCallback((action: string, value?: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "command", action, value }));
    }
  }, []);

  return { sendCommand, disconnect, connect };
}
