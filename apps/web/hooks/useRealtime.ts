import { createContext, useContext, useEffect, useState } from "react";

export const RealtimeContext = createContext({ tick: 0, connected: false });
export const useRealtime = () => useContext(RealtimeContext);

export function useWorkspaceStream(workspaceId: string) {
  const [state, setState] = useState({ tick: 0, connected: false });
  useEffect(() => {
    let disposed = false,
      cursor = 0,
      retry: ReturnType<typeof setTimeout>,
      socket: WebSocket;
    function connect() {
      const url = new URL(
        "/api/v1/ws",
        import.meta.env.VITE_API_URL || window.location.origin,
      );
      url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
      if (cursor) url.searchParams.set("after", String(cursor));
      socket = new WebSocket(url);
      socket.onmessage = (e) => {
        const event = JSON.parse(e.data);
        if (disposed) return;
        cursor = event.id ?? event.cursor ?? cursor;
        setState((prev) => ({
          connected: true,
          tick: prev.tick + (event.type !== "heartbeat" ? 1 : 0),
        }));
      };
      socket.onclose = () => {
        if (!disposed) {
          setState((prev) => ({ ...prev, connected: false }));
          retry = setTimeout(connect, 3000);
        }
      };
      socket.onerror = () => socket.close();
    }
    setState({ tick: 0, connected: false });
    connect();
    // Also refresh when a tab wakes and while a socket is reconnecting.
    const refresh = () =>
      setState((prev) => ({ ...prev, tick: prev.tick + 1 }));
    window.addEventListener("focus", refresh);
    const fallback = setInterval(refresh, 15000);
    return () => {
      disposed = true;
      clearTimeout(retry);
      clearInterval(fallback);
      socket?.close();
      window.removeEventListener("focus", refresh);
    };
  }, [workspaceId]);
  return state;
}
