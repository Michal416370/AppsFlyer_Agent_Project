# AppsFlyer ADK UI (dev)

This is a minimal Vite + React + TypeScript UI for rendering ADK component events (e.g. `AnomalyVisualizationDashboard`).

Run locally:

```bash
cd AppsFlyerAgent/ui
npm install
npm run dev
```

Usage:
- The UI expects the backend to send ADK events containing `component` definitions with `type: 'react_component'` and `name: 'AnomalyVisualizationDashboard'`.
- You can press "Simulate anomaly event" in the app to test locally.

Integration:
- Replace the placeholder `subscribeToAdkEvents` in `src/App.tsx` with your ADK event subscription (WebSocket, SDK, etc.).
- Ensure the backend `react_visual_agent` yields Events with `component` payload as described.
