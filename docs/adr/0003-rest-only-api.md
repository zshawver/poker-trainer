# REST-only API; no WebSocket

All client/server traffic is request/reply over HTTP. The `python-socketio` dependency in `pyproject.toml` is removed.

The reason WebSocket was on the table at all is the visual experience of "Villains act one at a time over ~2 seconds" — a streamed reveal of bot Actions. This is achievable just as well by returning the full Action sequence from a single REST call and animating the reveal client-side with `setTimeout`. The math is computed instantly server-side either way; the streamed feel is a UI concern, not a transport concern.

## Considered options

- **REST only** (chosen).
- **REST + WebSocket for the Action loop** — rejected. Adds reconnect logic, heartbeat, WS-auth handshake, and a second testing surface. Justifiable only if pushed events become a real product feature (live leaderboards, multiplayer), neither of which is in scope.
- **WebSocket only** — rejected. Hard to debug without curl/Postman; harder to cache; uncommon for turn-based games.

## Consequences

- API is fully describable as OpenAPI (FastAPI generates this for free).
- No persistent connection management on the server.
- Future "live multiplayer" or "live leaderboard" features will need a new ADR to add WS, and that ADR is fine to write *if and when* it matters.
