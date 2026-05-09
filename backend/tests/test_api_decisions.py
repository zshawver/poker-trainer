"""Happy-path integration tests for /api/decisions/* endpoints.

Each test posts a canonical reference body and asserts both the computed
value and that the inputs are echoed back per the acceptance criteria.
"""

import pytest


pytestmark = pytest.mark.anyio


async def test_pot_odds_endpoint(client):
    resp = await client.post("/api/decisions/pot-odds", json={"pot": 100, "bet_to_call": 50})
    assert resp.status_code == 200
    body = resp.json()
    assert body["pot_odds"] == pytest.approx(1 / 3)
    assert body["pot"] == 100
    assert body["bet_to_call"] == 50


async def test_required_equity_endpoint(client):
    resp = await client.post("/api/decisions/required-equity", json={"pot": 100, "bet_to_call": 50})
    assert resp.status_code == 200
    body = resp.json()
    assert body["required_equity"] == pytest.approx(1 / 3)
    assert body["pot"] == 100
    assert body["bet_to_call"] == 50


async def test_ev_endpoint_pure_call(client):
    # 50% equity calling 50 into pot of 100 (final pot 150)
    # EV = 0.5 * 150 - 50 = 25
    resp = await client.post(
        "/api/decisions/ev",
        json={"equity": 0.5, "pot": 100, "bet": 50, "fold_freq": 0.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["expected_value"] == pytest.approx(25.0)
    assert body["equity"] == 0.5
    assert body["pot"] == 100
    assert body["bet"] == 50
    assert body["fold_freq"] == 0.0


async def test_ev_endpoint_default_fold_freq(client):
    # Omitting fold_freq should default to 0.0
    resp = await client.post(
        "/api/decisions/ev",
        json={"equity": 0.5, "pot": 100, "bet": 50},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["expected_value"] == pytest.approx(25.0)
    assert body["fold_freq"] == 0.0


async def test_ev_endpoint_break_even_at_required_equity(client):
    # Cross-endpoint regression: required_equity returned from one
    # endpoint, plugged into ev with no fold equity, must give 0.
    re_resp = await client.post(
        "/api/decisions/required-equity",
        json={"pot": 100, "bet_to_call": 50},
    )
    eq = re_resp.json()["required_equity"]

    ev_resp = await client.post(
        "/api/decisions/ev",
        json={"equity": eq, "pot": 100, "bet": 50, "fold_freq": 0.0},
    )
    assert ev_resp.status_code == 200
    assert ev_resp.json()["expected_value"] == pytest.approx(0.0, abs=1e-9)


async def test_fold_equity_endpoint(client):
    resp = await client.post("/api/decisions/fold-equity", json={"pot": 100, "fold_freq": 0.4})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fold_equity"] == pytest.approx(40.0)
    assert body["pot"] == 100
    assert body["fold_freq"] == 0.4


async def test_mdf_endpoint(client):
    resp = await client.post("/api/decisions/mdf", json={"pot": 100, "bet": 50})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mdf"] == pytest.approx(2 / 3)
    assert body["pot"] == 100
    assert body["bet"] == 50
