# Poker Trainer

A poker math training program. The backend is a fast, NumPy-vectorized 7-card hand evaluator with an equity engine (precomputed 169×169 preflop lookup table), an interactive game loop, and an archetype-driven villain bot. A FastAPI/React layer is scaffolded on top for a future web UI.

## Setup

### Prerequisites

- [Anaconda](https://www.anaconda.com/) — for local backend dev
- [Node.js](https://nodejs.org/) (v18+) — for local frontend dev (when the UI exists)
- [Docker](https://www.docker.com/) and Docker Compose — for running the backend + Postgres stack

### Local backend dev

```bash
cd backend
conda env create -f environment.yml
conda activate poker_trainer
pip install -e .
pytest tests/                         # run evaluator tests
python -m src.engine.precompute_equity  # rebuild the 169x169 preflop table (~5-10 min)
uvicorn src.main:app --reload --port 8000
```

### Local frontend dev

```bash
cd frontend
npm install
npm run dev
```

### Quick start (Docker)

From the repo root:

```powershell
docker compose up --build
```

- Backend API: http://localhost:8000 (health check at `/api/health`)
- PostgreSQL: localhost:5432

The `frontend` service is gated behind the `frontend` Compose profile until its Dockerfile lands, so it is skipped by default. Once the frontend Dockerfile exists, run `docker compose --profile frontend up --build` to bring up the SPA on http://localhost:5173.

### Database migrations

```bash
cd backend
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "description"  # create migration
```

## Project layout

- `backend/src/engine/` — vectorized poker engine (cards, evaluator, equity, lookups)
- `backend/src/services/` — game orchestration and villain bot
- `backend/src/{api,core,db,models,schemas}/` — FastAPI scaffolding (not yet wired to the engine)
- `backend/tests/` — pytest suite
- `frontend/` — React/Vite scaffolding (no poker UI yet)
- `docs/` — project notes

## Notes

The 169×169 preflop equity table at `backend/src/engine/preflop_equity.json` is checked in as generated data (~800 KB). Regenerate it with `python -m src.engine.precompute_equity` from `backend/`.
