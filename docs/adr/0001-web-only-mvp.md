# Web-only MVP; mobile and Flutter deferred

The trainer is shipped as a browser-based React app for the foundation. Native mobile (Flutter, React Native) is out of scope for MVP and will be revisited only after the trainer concept has been validated with real use. The reasoning is scope: native mobile would require a second client codebase, App Store review, secure-storage token flows, and offline-first design — none of which pay back before we know whether the trainer teaches anything useful.

The backend's REST/JSON shape is deliberately client-agnostic so that a future Flutter or React Native client can be added without changing the API.

## Considered options

- **Web-only** (chosen) — single React/Vite codebase, fastest to MVP.
- **PWA (Progressive Web App)** — also single codebase, gives "Add to Home Screen" app-like behavior. Not chosen for MVP because PWA polish (offline, manifest, service worker) is its own sub-project.
- **Web + Flutter native** — initially chosen during grilling, then reversed once the user identified that the mobile commitment was scope-creep before any trainer behavior had shipped.

## Consequences

- The `frontend/` directory's React/Vite/Tailwind/Zustand scaffolding is the canonical client and stays.
- No Dockerfile is built for the frontend (`vite build` static assets go to a CDN later).
- The `docs/plan-frontend-project` branch's planning continues to target React.
