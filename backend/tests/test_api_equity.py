"""Integration tests for POST /api/equity.

Exercises both the ``vs_hand`` and ``vs_range`` paths, the preflop lookup
short-circuit, and the Pydantic 422 surface for malformed input.

Run from backend/: pytest tests/test_api_equity.py
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Happy-path smoke tests — both villain shapes, both streets
# ---------------------------------------------------------------------------

def test_vs_hand_river_exact(client: TestClient) -> None:
    """Hero with the nuts on the river -> equity 1.0, by_hand omitted."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_hand": ["Qc", "Qd"],
            "board": ["Qs", "Js", "Ts", "2c", "3d"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["equity"] == 1.0
    assert data["win"] == 1.0
    assert data["tie"] == 0.0
    assert data["lose"] == 0.0
    # by_hand is the range-only breakdown; vs_hand calls leave it null.
    assert data["by_hand"] is None


def test_vs_range_preflop_uses_lookup(client: TestClient) -> None:
    """Preflop vs_range request returns the lookup-table breakdown."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_range": ["AA", "KK", "QQ"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["by_hand"] is not None
    assert set(data["by_hand"].keys()) == {"AA", "KK", "QQ"}
    # AKs vs {AA, KK, QQ} is heavily dominated -> equity in the low 30s.
    assert 0.25 < data["equity"] < 0.40


def test_vs_range_river_exact(client: TestClient) -> None:
    """Range-equity on a river that gives Hero the nuts -> equity 1.0."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_range": ["QQ", "JJ"],
            "board": ["Qs", "Js", "Ts", "2c", "3d"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["equity"] == 1.0
    assert data["by_hand"]["QQ"] == 1.0
    assert data["by_hand"]["JJ"] == 1.0


def test_preflop_omitted_board_treated_as_empty(client: TestClient) -> None:
    """Sending board=null and omitting board entirely both work preflop."""
    payload_null = {
        "hero": ["As", "Ad"],
        "vs_hand": ["Ks", "Kd"],
        "board": None,
    }
    payload_omit = {
        "hero": ["As", "Ad"],
        "vs_hand": ["Ks", "Kd"],
    }
    r1 = client.post("/api/equity", json=payload_null).json()
    r2 = client.post("/api/equity", json=payload_omit).json()
    assert r1 == r2


# ---------------------------------------------------------------------------
# Pydantic validation surface (422 errors)
# ---------------------------------------------------------------------------

def test_both_villain_fields_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ad"],
            "vs_hand": ["Ks", "Kd"],
            "vs_range": ["QQ"],
        },
    )
    assert response.status_code == 422


def test_neither_villain_field_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/equity",
        json={"hero": ["As", "Ad"]},
    )
    assert response.status_code == 422


def test_invalid_card_string_rejected(client: TestClient) -> None:
    """Cards must match `[23456789TJQKA][chds]`; 'Zx' fails the regex."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Zx"],
            "vs_hand": ["Ks", "Kd"],
        },
    )
    assert response.status_code == 422


def test_invalid_hand_type_rejected(client: TestClient) -> None:
    """Hand-type strings must be one of the canonical 169."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_range": ["AA", "NotAHand"],
        },
    )
    assert response.status_code == 422


def test_invalid_board_length_rejected(client: TestClient) -> None:
    """Boards must be 0/3/4/5 cards; 2 cards is invalid."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_hand": ["Qc", "Qd"],
            "board": ["2c", "3d"],
        },
    )
    assert response.status_code == 422


def test_duplicate_card_across_hero_and_villain_rejected(
    client: TestClient,
) -> None:
    """As cannot be in both hero and vs_hand."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_hand": ["As", "Kd"],
        },
    )
    assert response.status_code == 422


def test_duplicate_card_across_hero_and_board_rejected(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_hand": ["Qc", "Qd"],
            "board": ["As", "Js", "Ts", "2c", "3d"],
        },
    )
    assert response.status_code == 422


def test_hero_must_have_two_cards(client: TestClient) -> None:
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As"],
            "vs_hand": ["Ks", "Kd"],
        },
    )
    assert response.status_code == 422


def test_empty_range_rejected(client: TestClient) -> None:
    """An empty vs_range list violates the min_length=1 constraint."""
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_range": [],
        },
    )
    assert response.status_code == 422
