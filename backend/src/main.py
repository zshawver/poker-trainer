from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, decisions, equity


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: initialize connections, run setup tasks
    yield
    # Shutdown: close connections, cleanup resources


app = FastAPI(title="Project Name", lifespan=lifespan)

# CORS — allow the Vite dev server origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(equity.router, prefix="/api/equity", tags=["equity"])


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
