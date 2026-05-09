"""Tests for the FSM rebuild of services/game.py per ADR-0005."""

import json
from dataclasses import FrozenInstanceError, asdict

import pytest

from src.services.game import (
    Action,
    BETTING_PHASES,
    Decision,
    Game,
    GameState,
    InvalidTransition,
    Phase,
    Seat,
)


# ============================================================
# Test helpers
# ============================================================

_RANK = {c: i for i, c in enumerate('23456789TJQKA')}
_SUIT = {c: i for i, c in enumerate('chds')}


def card(s: str) -> int:
    """'Ah' -> 49 (rank * 4 + suit)."""
    return _RANK[s[0]] * 4 + _SUIT[s[1]]


def deck_with(head_cards: list[int]) -> tuple[int, ...]:
    """Build a 52-card permutation with `head_cards` first, fillers in order after."""
    used = set(head_cards)
    if len(used) != len(head_cards):
        raise ValueError("duplicate cards in head")
    fillers = [c for c in range(52) if c not in used]
    return tuple(head_cards + fillers)


# Deal order at N=3:
#   seat 0 (Hero/BTN) gets deck[0:2]
#   seat 1 (V1/SB)    gets deck[2:4]
#   seat 2 (V2/BB)    gets deck[4:6]
# Then burn[6], flop[7:10], burn[10], turn[11], burn[12], river[13].
SHOWDOWN_DECK_HEAD = [
    card('Ah'), card('Kh'),                # Hero hole
    card('2c'), card('7d'),                # V1 hole
    card('4s'), card('9c'),                # V2 hole
    card('2d'),                            # burn 1
    card('As'), card('Kd'), card('Qc'),    # flop
    card('2s'),                            # burn 2
    card('Jh'),                            # turn
    card('3c'),                            # burn 3
    card('2h'),                            # river
]


def make_game_3(deck: tuple[int, ...] | None = None, big_blind: int = 10) -> Game:
    """Standard 3-seat game: Hero=BTN(0), V1=SB(1), V2=BB(2)."""
    if deck is None:
        deck = deck_with(SHOWDOWN_DECK_HEAD)
    return Game(
        seat_specs=[("Hero", 1000, True), ("V1", 1000, False), ("V2", 1000, False)],
        big_blind=big_blind,
        deck=deck,
    )


# ============================================================
# Phase factories — each returns a Game in the named Phase
# ============================================================

def at_waiting_for_blinds() -> Game:
    return make_game_3()


def at_preflop_betting() -> Game:
    g = make_game_3()
    g.post_blinds()
    return g


def at_waiting_for_flop() -> Game:
    g = at_preflop_betting()
    # 3-way limp: Hero (BTN) calls, V1 (SB) completes, V2 (BB) checks option.
    g.call("Hero")
    g.call("V1")
    g.check("V2")
    return g


def at_flop_betting() -> Game:
    g = at_waiting_for_flop()
    g.deal_flop()
    return g


def at_waiting_for_turn() -> Game:
    g = at_flop_betting()
    g.check("V1"); g.check("V2"); g.check("Hero")
    return g


def at_turn_betting() -> Game:
    g = at_waiting_for_turn()
    g.deal_turn()
    return g


def at_waiting_for_river() -> Game:
    g = at_turn_betting()
    g.check("V1"); g.check("V2"); g.check("Hero")
    return g


def at_river_betting() -> Game:
    g = at_waiting_for_river()
    g.deal_river()
    return g


def at_showdown() -> Game:
    g = at_river_betting()
    g.check("V1"); g.check("V2"); g.check("Hero")
    return g


def at_hand_complete() -> Game:
    g = at_showdown()
    g.showdown()
    return g


FACTORY_FOR_PHASE = {
    Phase.WaitingForBlinds: at_waiting_for_blinds,
    Phase.PreflopBetting:   at_preflop_betting,
    Phase.WaitingForFlop:   at_waiting_for_flop,
    Phase.FlopBetting:      at_flop_betting,
    Phase.WaitingForTurn:   at_waiting_for_turn,
    Phase.TurnBetting:      at_turn_betting,
    Phase.WaitingForRiver:  at_waiting_for_river,
    Phase.RiverBetting:     at_river_betting,
    Phase.Showdown:         at_showdown,
    Phase.HandComplete:     at_hand_complete,
}


# ============================================================
# Phase x Action validity matrix
# ============================================================

ALL_OPS = (
    'post_blinds', 'fold', 'check', 'call', 'bet', 'raise_to',
    'deal_flop', 'deal_turn', 'deal_river', 'showdown',
)

EXPECTED: dict[tuple[Phase, str], str] = {}


def _expect(phase: Phase, **ok_ops):
    """All ops default to 'raises' unless explicitly marked 'ok'."""
    for op in ALL_OPS:
        EXPECTED[(phase, op)] = ok_ops.get(op, 'raises')


# Each factory leaves the round at its start (current_bet = BB preflop, 0 postflop),
# so state-dependent ops (check facing a bet, call when nothing to call, etc.) raise.
_expect(Phase.WaitingForBlinds, post_blinds='ok')
_expect(Phase.PreflopBetting,   fold='ok', call='ok', raise_to='ok')
_expect(Phase.WaitingForFlop,   deal_flop='ok')
_expect(Phase.FlopBetting,      fold='ok', check='ok', bet='ok')
_expect(Phase.WaitingForTurn,   deal_turn='ok')
_expect(Phase.TurnBetting,      fold='ok', check='ok', bet='ok')
_expect(Phase.WaitingForRiver,  deal_river='ok')
_expect(Phase.RiverBetting,     fold='ok', check='ok', bet='ok')
_expect(Phase.Showdown,         showdown='ok')
_expect(Phase.HandComplete)


def _invoke(g: Game, op: str):
    """Call `op` against `g` using the seat that's currently to-act (when applicable)."""
    actor = (
        g.state.seats[g.state.to_act_idx].name
        if g.state.to_act_idx >= 0 else "Hero"
    )
    if op == 'post_blinds': return g.post_blinds()
    if op == 'fold':        return g.fold(actor)
    if op == 'check':       return g.check(actor)
    if op == 'call':        return g.call(actor)
    if op == 'bet':         return g.bet(actor, 10)        # exactly the min bet
    if op == 'raise_to':    return g.raise_to(actor, 20)   # min legal raise vs BB=10
    if op == 'deal_flop':   return g.deal_flop()
    if op == 'deal_turn':   return g.deal_turn()
    if op == 'deal_river':  return g.deal_river()
    if op == 'showdown':    return g.showdown()
    raise ValueError(f"unknown op {op!r}")


@pytest.mark.parametrize("phase,op", sorted(EXPECTED.keys(), key=lambda pair: (pair[0].value, pair[1])))
def test_phase_action_matrix(phase: Phase, op: str):
    """Every (Phase, op) cell either succeeds or raises InvalidTransition."""
    g = FACTORY_FOR_PHASE[phase]()
    expected = EXPECTED[(phase, op)]
    if expected == 'ok':
        _invoke(g, op)
    else:
        with pytest.raises(InvalidTransition):
            _invoke(g, op)


# ============================================================
# Enum and dataclass invariants
# ============================================================

def test_phase_enum_has_ten_values():
    assert len(list(Phase)) == 10


def test_phase_values_match_adr_0005_spec():
    assert {p.value for p in Phase} == {
        "WaitingForBlinds", "PreflopBetting",
        "WaitingForFlop", "FlopBetting",
        "WaitingForTurn", "TurnBetting",
        "WaitingForRiver", "RiverBetting",
        "Showdown", "HandComplete",
    }


def test_state_is_frozen():
    g = make_game_3()
    with pytest.raises(FrozenInstanceError):
        g.state.phase = Phase.HandComplete  # type: ignore[misc]


def test_state_seats_are_frozen():
    g = make_game_3()
    with pytest.raises(FrozenInstanceError):
        g.state.seats[0].stack = 0  # type: ignore[misc]


def test_state_json_serializable_at_every_phase():
    """asdict(state) must be directly accepted by json.dumps in every Phase."""
    for phase, factory in FACTORY_FOR_PHASE.items():
        g = factory()
        json.dumps(asdict(g.state))


# ============================================================
# Forward-transition smoke (deterministic full hand)
# ============================================================

def test_full_hand_walks_every_phase():
    """3-way limp-and-check-down hand. Asserts each Phase transition + final winner."""
    g = make_game_3()
    assert g.state.phase == Phase.WaitingForBlinds

    g.post_blinds()
    assert g.state.phase == Phase.PreflopBetting
    assert g.state.pot == 15                                   # SB(5) + BB(10)
    assert g.state.seats[g.state.to_act_idx].name == "Hero"   # BTN acts first preflop at N=3

    g.call("Hero")     # limp to 10
    g.call("V1")       # SB completes to 10
    g.check("V2")      # BB checks option
    assert g.state.phase == Phase.WaitingForFlop
    assert g.state.pot == 30

    g.deal_flop()
    assert g.state.phase == Phase.FlopBetting
    assert g.state.board == (card('As'), card('Kd'), card('Qc'))
    g.check("V1"); g.check("V2"); g.check("Hero")
    assert g.state.phase == Phase.WaitingForTurn

    g.deal_turn()
    assert g.state.phase == Phase.TurnBetting
    assert g.state.board[3] == card('Jh')
    g.check("V1"); g.check("V2"); g.check("Hero")
    assert g.state.phase == Phase.WaitingForRiver

    g.deal_river()
    assert g.state.phase == Phase.RiverBetting
    assert g.state.board[4] == card('2h')
    g.check("V1"); g.check("V2"); g.check("Hero")
    assert g.state.phase == Phase.Showdown

    g.showdown()
    assert g.state.phase == Phase.HandComplete
    # Hero (Ah Kh) on As Kd Qc Jh 2h has top two pair AAKK and beats both villains.
    assert g.state.winners == ("Hero",)
    hero = next(s for s in g.state.seats if s.is_hero)
    assert hero.stack == 1000 - 10 + 30


# ============================================================
# Auto-advance villains (placeholder rule: fold-or-check)
# ============================================================

def test_auto_advance_preflop_foldout():
    """Hero opens, both villains fold to the bet, hand ends preflop."""
    g = make_game_3()
    g.post_blinds()
    g.raise_to("Hero", 30)         # 3x BB open
    g.auto_advance_villains()

    assert g.state.phase == Phase.HandComplete
    assert g.state.winners == ("Hero",)
    hero = next(s for s in g.state.seats if s.is_hero)
    # Hero's net = +SB+BB = +15. 30 invested, 45 won (5 SB + 10 BB + 30 self).
    assert hero.stack == 1015


def test_auto_advance_walks_to_showdown():
    """Hero limps; placeholder villains fold/check through every street to Showdown."""
    g = make_game_3()
    g.post_blinds()

    g.call("Hero")                 # Hero limps
    g.auto_advance_villains()
    # V1 (SB) faces 5-more-to-call → folds. V2 (BB) checks for free. Round settles.
    assert g.state.phase == Phase.WaitingForFlop

    g.deal_flop()
    g.auto_advance_villains()
    assert g.state.seats[g.state.to_act_idx].is_hero
    g.check("Hero")
    assert g.state.phase == Phase.WaitingForTurn

    g.deal_turn()
    g.auto_advance_villains()
    g.check("Hero")
    assert g.state.phase == Phase.WaitingForRiver

    g.deal_river()
    g.auto_advance_villains()
    g.check("Hero")
    assert g.state.phase == Phase.Showdown

    g.showdown()
    assert g.state.phase == Phase.HandComplete
    assert "Hero" in g.state.winners


# ============================================================
# State-level invariants (out-of-turn, min raise, bet vs raise)
# ============================================================

def test_action_out_of_turn_raises():
    g = make_game_3()
    g.post_blinds()
    # Hero is to_act (BTN at N=3); asking V1 to fold is out-of-turn.
    with pytest.raises(InvalidTransition):
        g.fold("V1")


def test_below_min_raise_rejected():
    g = make_game_3()
    g.post_blinds()
    # current_bet=10, last_raise_increment=10, so min legal raise total = 20.
    with pytest.raises(InvalidTransition):
        g.raise_to("Hero", 15)
    # Min legal raise (to 20) succeeds.
    g.raise_to("Hero", 20)
    assert g.state.current_bet == 20


def test_bet_when_facing_bet_rejected():
    g = make_game_3()
    g.post_blinds()
    # Preflop has current_bet=10 from BB; bet() must reject in favor of raise_to().
    with pytest.raises(InvalidTransition):
        g.bet("Hero", 30)


def test_unknown_seat_raises():
    g = make_game_3()
    g.post_blinds()
    with pytest.raises(InvalidTransition):
        g.fold("not-a-seat")


def test_raise_to_when_no_bet_rejected():
    """Postflop with no bet open, raise_to() should reject (use bet() instead)."""
    g = at_flop_betting()
    with pytest.raises(InvalidTransition):
        g.raise_to("V1", 50)


def test_call_when_nothing_to_call_rejected():
    """Postflop with no bet open, call() should reject (use check() instead)."""
    g = at_flop_betting()
    with pytest.raises(InvalidTransition):
        g.call("V1")


# ============================================================
# Decision recording
# ============================================================

def test_only_hero_actions_become_decisions():
    """Action log captures everyone; Decision log captures Hero only."""
    g = make_game_3()
    g.post_blinds()
    g.call("Hero")
    g.call("V1")
    g.check("V2")

    assert [a.seat_name for a in g.state.actions] == ["Hero", "V1", "V2"]
    assert len(g.state.decisions) == 1
    d = g.state.decisions[0]
    assert d.seat_name == "Hero"
    assert d.action == Action.CALL
    assert d.amount == 10
    assert d.bet_to_call == 10              # Hero faced 10 to call
    assert d.equity is None                  # math wired in by issue #4
    assert d.pot_odds is None
