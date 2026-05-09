"""Integration tests for POST /api/evaluate."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.engine.cards import parse_cards
from src.engine.evaluator import CATEGORY_SCALE, evaluate_hands
from src.main import app


# Local override of the conftest `client` fixture: the conftest version is
# `@pytest.fixture` on an async function, which pytest-asyncio's strict mode
# does not support. Decorating with `@pytest_asyncio.fixture` here makes it
# work without modifying conftest.py.
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_evaluate_royal_flush_matches_engine(client):
    cards = ["As", "Ks", "Qs", "Js", "Ts", "2c", "3d"]
    response = await client.post("/api/evaluate", json={"cards": cards})

    assert response.status_code == 200
    body = response.json()

    expected_score = int(evaluate_hands(parse_cards(cards).reshape(1, 7))[0])
    expected_category = expected_score // int(CATEGORY_SCALE)

    assert body["score"] == expected_score
    assert body["category"] == expected_category
    assert body["category_name"] == "royal_flush"


@pytest.mark.asyncio
async def test_evaluate_rejects_wrong_card_count(client):
    response = await client.post("/api/evaluate", json={"cards": ["As", "Ks"]})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_evaluate_rejects_invalid_card_string(client):
    cards = ["Zs", "Ks", "Qs", "Js", "Ts", "2c", "3d"]
    response = await client.post("/api/evaluate", json={"cards": cards})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_evaluate_rejects_duplicate_cards(client):
    cards = ["As", "As", "Qs", "Js", "Ts", "2c", "3d"]
    response = await client.post("/api/evaluate", json={"cards": cards})
    assert response.status_code == 422
