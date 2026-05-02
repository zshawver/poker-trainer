# Project Name

## Description

<!-- Brief description of what this project does. -->

## Setup

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Node.js](https://nodejs.org/) (v18+) — for local frontend dev
- [Anaconda](https://www.anaconda.com/) — for local backend dev

### Quick start (Docker)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Local frontend dev

```bash
cd frontend
npm install
npm run dev
```

### Local backend dev

```bash
cd backend
conda env create -f environment.yml
conda activate project_name
uvicorn src.main:app --reload --port 8000
```

### Database migrations

```bash
cd backend
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "description"  # create migration
```

## How to Run

<!-- Instructions for running the main workflow. -->

## Data Sources

<!-- Where does the data come from? How is it refreshed? -->

## Notes

<!-- Any additional context, caveats, or references. -->
