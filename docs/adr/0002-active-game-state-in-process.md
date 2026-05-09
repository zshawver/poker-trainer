# Active game state lives in process memory; only completed Hands persist

While a **Hand** is in progress, its **HandState** lives in a Python dict on the FastAPI server, keyed by game id. When a Hand reaches the `HandComplete` phase, it is materialized into the `completed_hands` and `hand_decisions` Postgres tables (see ADR-0007) and removed from process memory. Active state is **not** persisted: a server restart drops in-flight Hands, and the user simply re-deals.

This is the deliberate trade-off for a single-user MVP. Persisting active HandState in Postgres (every Action becomes a write) or in Redis (introduces a second stateful service) costs real code and operational surface to solve a problem — "what if the server restarts mid-Hand?" — that we do not have at MVP volume with one user.

## Consequences

- The browser holds its own copy of the visible state for rendering, but the server is authoritative for cards and pot.
- Closing the browser tab mid-Hand abandons the Hand. The Hand is not in `completed_hands`.
- Horizontal scaling is not supported by this design. The backend runs as a single process. Multi-process deploy is a future ADR if we ever need it.
- No `from_dict` is needed on `HandState` to round-trip through storage. `to_dict` is still needed for HTTP responses.
- `python-socketio` and Redis are not needed and can be dropped from `pyproject.toml` and `docker-compose.yml` respectively (see also ADR-0003).
