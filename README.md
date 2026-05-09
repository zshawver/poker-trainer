# Poker Trainer

A poker math training program. The backend is a fast, NumPy-vectorized 7-card hand evaluator with an equity engine (precomputed 169×169 preflop lookup table), an interactive game loop, and an archetype-driven villain bot. A FastAPI/React layer is scaffolded on top for a future web UI.

## Setup

### Prerequisites

- [Anaconda](https://www.anaconda.com/) — for local backend dev
- [Node.js](https://nodejs.org/) (v18+) — for local frontend dev (when the UI exists)
- [Docker](https://www.docker.com/) and Docker Compose — for the full stack with Postgres/Redis

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

### Quick start (Docker, once Dockerfiles exist)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5434 (mapped to container `:5432`)
- Redis: localhost:6379

### Database migrations

```bash
cd backend
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "description"  # create migration
```

### Admin: create a user

There is no public signup (see `docs/adr/0004-invite-only-auth.md`). New users
are created via the seed CLI against a running Postgres:

```powershell
cd backend
python -m scripts.seed --create-user EMAIL PASSWORD          # regular user
python -m scripts.seed --create-user EMAIL PASSWORD --admin  # admin user
```

### Tests

Integration tests need a Postgres instance reachable at the URL in
`TEST_DATABASE_URL` (default `postgresql+asyncpg://postgres:postgres@localhost:5434/app_test`).
Start the docker-compose `db` service, then run pytest from `backend/`. The
test DB is created on first run and tables are dropped at session end.

## Project layout

- `backend/src/engine/` — vectorized poker engine (cards, evaluator, equity, lookups)
- `backend/src/services/` — game orchestration and villain bot
- `backend/src/{api,core,db,models,schemas}/` — FastAPI scaffolding (not yet wired to the engine)
- `backend/tests/` — pytest suite
- `frontend/` — React/Vite scaffolding (no poker UI yet)
- `docs/` — project notes

## Notes

The 169×169 preflop equity table at `backend/src/engine/preflop_equity.json` is checked in as generated data (~800 KB). Regenerate it with `python -m src.engine.precompute_equity` from `backend/`.
