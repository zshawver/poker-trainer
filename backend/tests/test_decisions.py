"""Unit tests for the pure-math decision helpers in engine/decisions.py."""

import pytest

from src.engine.decisions import (
    expected_value,
    fold_equity,
    minimum_defense_frequency,
    pot_odds,
    required_equity,
)


# ========== pot_odds ==========


def test_pot_odds_canonical_third():
    # Canonical CONTEXT.md example: pot 100, facing a 50 bet → 1/3
    assert pot_odds(100, 50) == pytest.approx(1 / 3)


def test_pot_odds_zero_call_returns_zero():
    # Nothing to call → no equity required (guard against 0/0)
    assert pot_odds(100, 0) == 0.0


def test_pot_odds_pot_sized_bet_is_one_third():
    # A pot-sized bet (villain bets X into pot of X) means the displayed pot
    # is 2X and bet_to_call is X → pot_odds = X / (2X + X) = 1/3.
    assert pot_odds(200, 100) == pytest.approx(1 / 3)
    assert pot_odds(15.0, 7.5) == pytest.approx(1 / 3)


def test_pot_odds_call_equal_to_pot_is_one_half():
    # bet_to_call equal to displayed pot → 0.5 (need 50% equity)
    assert pot_odds(200, 200) == pytest.approx(0.5)


def test_pot_odds_half_pot_bet_returns_one_quarter():
    # Half-pot bet (50 into 200) → 50 / 250 = 0.2
    assert pot_odds(200, 50) == pytest.approx(0.2)


# ========== required_equity (alias) ==========


def test_required_equity_equals_pot_odds():
    # Synonym per CONTEXT.md — must agree across a range of inputs
    for pot, btc in [(100, 50), (200, 200), (7.5, 2.5), (1000, 0)]:
        assert required_equity(pot, btc) == pot_odds(pot, btc)


# ========== expected_value ==========


def test_ev_pure_call_even_money():
    # Calling 50 into a pot of 100 (final pot 150) with 50% equity
    # EV = 0 + 1.0 * (0.5 * 150 - 50) = 75 - 50 = 25
    assert expected_value(equity=0.5, pot=100, bet=50, fold_freq=0.0) == pytest.approx(25.0)


def test_ev_pure_fold_equity():
    # Villain always folds → win the existing pot regardless of equity
    assert expected_value(equity=0.0, pot=100, bet=50, fold_freq=1.0) == pytest.approx(100.0)


def test_ev_always_win_called():
    # 100% equity, called every time → win the existing pot
    # EV = 0 + 1.0 * (1.0 * 150 - 50) = 150 - 50 = 100
    assert expected_value(equity=1.0, pot=100, bet=50, fold_freq=0.0) == pytest.approx(100.0)


def test_ev_mixed_fold_and_equity():
    # 30% folds, 40% equity when called, pot 100, bet 50
    # EV = 0.3 * 100 + 0.7 * (0.4 * 150 - 50)
    #    = 30 + 0.7 * 10 = 30 + 7 = 37
    assert expected_value(equity=0.4, pot=100, bet=50, fold_freq=0.3) == pytest.approx(37.0)


def test_ev_zero_equity_zero_fold_loses_bet():
    # Dead money — bet is just lost
    assert expected_value(equity=0.0, pot=100, bet=50, fold_freq=0.0) == pytest.approx(-50.0)


def test_ev_default_fold_freq_is_zero():
    # Default kwarg matches explicit 0.0
    assert expected_value(0.5, 100, 50) == expected_value(0.5, 100, 50, fold_freq=0.0)


@pytest.mark.parametrize(
    "pot,bet_to_call",
    [(100, 50), (200, 100), (15.0, 7.5), (250, 75), (1, 1)],
)
def test_ev_breaks_even_at_required_equity(pot, bet_to_call):
    # Regression: pot_odds defines the break-even equity for a call,
    # so plugging required_equity into expected_value with no fold
    # equity must return 0. This pins the EV formula to the same
    # `pot`-semantics as pot_odds / required_equity.
    eq = required_equity(pot, bet_to_call)
    ev = expected_value(equity=eq, pot=pot, bet=bet_to_call, fold_freq=0.0)
    assert ev == pytest.approx(0.0, abs=1e-9)


# ========== fold_equity ==========


def test_fold_equity_canonical():
    # CONTEXT.md: villain_fold_freq * pot
    assert fold_equity(pot=100, fold_freq=0.4) == pytest.approx(40.0)


def test_fold_equity_zero_freq_is_zero():
    assert fold_equity(pot=100, fold_freq=0.0) == 0.0


def test_fold_equity_full_fold_returns_pot():
    assert fold_equity(pot=250, fold_freq=1.0) == pytest.approx(250.0)


# ========== minimum_defense_frequency ==========


def test_mdf_canonical_two_thirds():
    # Canonical CONTEXT.md example: pot 100, bet 50 → 2/3
    assert minimum_defense_frequency(100, 50) == pytest.approx(2 / 3)


def test_mdf_zero_bet_returns_zero():
    # Guard against 0/0 — no bet faced, no defense required
    assert minimum_defense_frequency(100, 0) == 0.0


def test_mdf_pot_sized_bet_is_one_half():
    # Pot-sized bet (B = P) → MDF = P / 2P = 0.5
    assert minimum_defense_frequency(200, 200) == pytest.approx(0.5)


def test_mdf_overbet_below_one_half():
    # 2x pot bet → MDF = 100 / 300 = 1/3
    assert minimum_defense_frequency(100, 200) == pytest.approx(1 / 3)
