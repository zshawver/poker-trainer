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


def test_vs_range_preflop_is_blocker_aware(client: TestClient) -> None:
    """Preflop vs_range result reflects hero's blockers on the villain range.

    Hero As Ks vs ["AA", "KK", "QQ"]: the As blocks 3 of 6 AA combos and the
    Ks blocks 3 of 6 KK combos, so AA and KK get half the weight they would
    in a flat 169-type average. Blocker-aware equity is ~0.345; a flat
    lookup would return ~0.305. The assertion's lower bound is set to
    exclude the lookup-style answer so regressions to the old behavior
    will fail this test.
    """
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
    # Blocker-aware ~0.345 (Monte Carlo). Lookup-style ~0.305 would fail this.
    assert 0.325 < data["equity"] < 0.375, (
        f"Expected ~0.345 (blocker-aware); got {data['equity']:.4f}"
    )


def test_vs_hand_preflop_preserves_concrete_suits(client: TestClient) -> None:
    """Preflop vs_hand uses the concrete cards, not the 169-type bucket.

    AhKd vs QhJd and AhKd vs QcJs both collapse to 'AKo vs QJo' in the
    169-type lookup and would return identical equity if we routed through
    it. With concrete-card evaluation, the actual equities diverge (~0.013
    apart, with the suit-clashing case slightly higher in practice). The
    direction is not the point — what matters is that the two responses
    are *not* identical.

    Tolerance: 25K-sample MC gives sigma~0.003 per call, so the
    two-call difference has sigma~0.004. Requiring |diff| > 0.005
    reliably catches a regression to lookup behavior (which would
    return |diff| = 0).
    """
    r_clash = client.post(
        "/api/equity",
        json={"hero": ["Ah", "Kd"], "vs_hand": ["Qh", "Jd"]},
    ).json()
    r_clean = client.post(
        "/api/equity",
        json={"hero": ["Ah", "Kd"], "vs_hand": ["Qc", "Js"]},
    ).json()
    diff = abs(r_clean["equity"] - r_clash["equity"])
    assert diff > 0.005, (
        f"Concrete suits ignored: clash={r_clash['equity']:.4f}, "
        f"clean={r_clean['equity']:.4f}, diff={diff:.4f}"
    )


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
    """Sending board=null and omitting board entirely both run the preflop path.

    Under the live engine, two independent calls produce non-identical
    results due to Monte Carlo sampling. The equivalence we care about is
    behavioral — both payloads return 200 and land on the same equity
    answer within MC noise.
    """
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
    # 25K-sample MC gives sigma~0.003; ±0.02 is a generous bound that
    # catches any structural divergence between the two payloads.
    assert abs(r1["equity"] - r2["equity"]) < 0.02


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


def test_duplicate_vs_range_rejected(client: TestClient) -> None:
    """Ranges are semantically sets; duplicates would silently re-weight.

    The aggregate equity calculation sums per list entry, so ['AA', 'AA',
    'KK'] would put AA at 2x the weight of KK -- a subtle bug. Reject at
    the schema boundary instead.
    """
    response = client.post(
        "/api/equity",
        json={
            "hero": ["As", "Ks"],
            "vs_range": ["AA", "AA", "KK"],
        },
    )
    assert response.status_code == 422
