"""
Hand-rolled FSM for a poker Hand. See ADR-0005.

Three layers:
1. ``Phase`` — the 10 discrete states the FSM walks through.
2. ``GameState`` — frozen dataclass snapshot. Transitions return a *new* GameState.
3. ``Game`` — ergonomic wrapper. Each method validates the current Phase, then
   replaces ``self.state`` with the next GameState.

JSON serialization: ``Phase`` and ``Action`` subclass ``str`` so
``dataclasses.asdict(state)`` is directly accepted by ``json.dumps``.

This module is Hero-only for the moment — Villains either get driven
explicitly by the caller (real bot logic lands in issue #7) or via the
placeholder ``auto_advance_villains`` rule (fold facing a bet, otherwise check).
"""

from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

from src.engine.cards import FULL_DECK
from src.engine.evaluator import evaluate_hands
from src.engine.positions import Positions


# ============================================================
# Enums
# ============================================================

class Phase(str, Enum):
    WaitingForBlinds = "WaitingForBlinds"
    PreflopBetting   = "PreflopBetting"
    WaitingForFlop   = "WaitingForFlop"
    FlopBetting      = "FlopBetting"
    WaitingForTurn   = "WaitingForTurn"
    TurnBetting      = "TurnBetting"
    WaitingForRiver  = "WaitingForRiver"
    RiverBetting     = "RiverBetting"
    Showdown         = "Showdown"
    HandComplete     = "HandComplete"


class Action(str, Enum):
    FOLD  = "fold"
    CHECK = "check"
    CALL  = "call"
    BET   = "bet"
    RAISE = "raise"


BETTING_PHASES: tuple[Phase, ...] = (
    Phase.PreflopBetting, Phase.FlopBetting,
    Phase.TurnBetting, Phase.RiverBetting,
)

# Map a WaitingFor* phase to the betting Phase it transitions into on a deal.
_DEAL_TARGET: dict[Phase, Phase] = {
    Phase.WaitingForFlop:  Phase.FlopBetting,
    Phase.WaitingForTurn:  Phase.TurnBetting,
    Phase.WaitingForRiver: Phase.RiverBetting,
}

# Map a betting Phase to the WaitingFor* (or Showdown) it advances to once
# the round settles.
_SETTLE_TARGET: dict[Phase, Phase] = {
    Phase.PreflopBetting: Phase.WaitingForFlop,
    Phase.FlopBetting:    Phase.WaitingForTurn,
    Phase.TurnBetting:    Phase.WaitingForRiver,
    Phase.RiverBetting:   Phase.Showdown,
}


class InvalidTransition(Exception):
    """Raised when an FSM action is attempted in an invalid Phase or against invalid state."""


# ============================================================
# Value objects (frozen, JSON-serializable via dataclasses.asdict)
# ============================================================

@dataclass(frozen=True)
class Seat:
    name: str
    position: str          # 'BTN', 'SB', 'BB', 'UTG', ... per Positions[n]
    is_hero: bool
    stack: int             # chips remaining
    hole: tuple[int, ...]  # 0 cards before deal, 2 card-IDs after
    is_active: bool        # False after fold; busted seats stay inactive between Hands
    street_bet: int        # chips committed in the current betting round
    all_in: bool


@dataclass(frozen=True)
class ActionRecord:
    """One Action by one seat. Blind posts are NOT Actions per CONTEXT.md."""
    seat_name: str
    action: Action
    amount: int            # chips moved from stack to pot for this Action
    phase: Phase


@dataclass(frozen=True)
class Decision:
    """A Hero Action enriched with its math context.

    Math fields are nullable for now — issue #4 (decision-math module) populates
    equity / pot_odds / ev_options when it lands.
    """
    seat_name: str
    action: Action
    amount: int
    phase: Phase
    pot_at_decision: int
    bet_to_call: int
    equity: float | None = None
    pot_odds: float | None = None
    ev_options: dict | None = None


@dataclass(frozen=True)
class GameState:
    phase: Phase
    seats: tuple[Seat, ...]
    to_act_idx: int                      # -1 when no seat is to act
    board: tuple[int, ...]
    pot: int
    street: str | None                   # 'preflop' | 'flop' | 'turn' | 'river' | None
    current_bet: int                     # max street_bet anyone has put in this round
    last_aggressor_idx: int | None
    last_raise_increment: int            # min legal next-raise = current_bet + this
    seats_to_act: tuple[int, ...]        # remaining indices owed a turn this round
    actions: tuple[ActionRecord, ...]
    decisions: tuple[Decision, ...]
    big_blind: int
    small_blind: int
    deck: tuple[int, ...]                # remaining cards; head is next to deal
    dealer_idx: int
    winners: tuple[str, ...]             # names of seats awarded the pot at HandComplete


# ============================================================
# Pure helpers
# ============================================================

def _seat_idx(state: GameState, name: str) -> int:
    for i, s in enumerate(state.seats):
        if s.name == name:
            return i
    raise InvalidTransition(f"Seat {name!r} not found in state")


def _replace_seat(seats: tuple[Seat, ...], idx: int, **changes) -> tuple[Seat, ...]:
    return seats[:idx] + (replace(seats[idx], **changes),) + seats[idx + 1:]


def _first_to_act_preflop(seats: tuple[Seat, ...]) -> int:
    """First active non-all-in seat after the BB (UTG at full ring)."""
    n = len(seats)
    bb_idx = next(i for i, s in enumerate(seats) if s.position == 'BB')
    for offset in range(1, n + 1):
        idx = (bb_idx + offset) % n
        if seats[idx].is_active and not seats[idx].all_in:
            return idx
    return -1


def _first_to_act_postflop(seats: tuple[Seat, ...]) -> int:
    """First active non-all-in seat starting from the SB."""
    n = len(seats)
    sb_idx = next(i for i, s in enumerate(seats) if s.position == 'SB')
    for offset in range(n):
        idx = (sb_idx + offset) % n
        if seats[idx].is_active and not seats[idx].all_in:
            return idx
    return -1


def _full_round_order(seats: tuple[Seat, ...], start_idx: int) -> tuple[int, ...]:
    """Active non-all-in seats in betting order, starting from start_idx, wrapping once."""
    n = len(seats)
    out: list[int] = []
    for offset in range(n):
        idx = (start_idx + offset) % n
        s = seats[idx]
        if s.is_active and not s.all_in:
            out.append(idx)
    return tuple(out)


def _response_order(seats: tuple[Seat, ...], aggressor_idx: int) -> tuple[int, ...]:
    """All OTHER active non-all-in seats starting from one past the aggressor."""
    n = len(seats)
    out: list[int] = []
    for offset in range(1, n):
        idx = (aggressor_idx + offset) % n
        s = seats[idx]
        if s.is_active and not s.all_in:
            out.append(idx)
    return tuple(out)


def _all_matched(seats: tuple[Seat, ...], current_bet: int) -> bool:
    return all(
        s.street_bet == current_bet
        for s in seats
        if s.is_active and not s.all_in
    )


# ============================================================
# Game wrapper
# ============================================================

class Game:
    """Imperative shell over an immutable GameState core.

    Each public method validates Phase, computes the next state, replaces
    ``self.state``, and returns the new state. Invalid (Phase, action)
    combinations raise ``InvalidTransition``.
    """

    state: GameState

    def __init__(
        self,
        seat_specs: list[tuple[str, int, bool]],
        big_blind: int = 10,
        small_blind: int | None = None,
        *,
        deck: tuple[int, ...] | None = None,
        rng: np.random.Generator | None = None,
        dealer_idx: int = 0,
    ):
        """seat_specs: list of (name, buy_in, is_hero). Exactly one Hero required.

        ``deck`` lets tests pin a deterministic deal order; otherwise a fresh
        shuffle of FULL_DECK is generated. Hole cards are dealt seat-by-seat
        from the head of the deck.
        """
        n = len(seat_specs)
        if n < 3 or n > 9:
            raise ValueError(f"Need 3-9 seats, got {n}")
        if sum(1 for _, _, h in seat_specs if h) != 1:
            raise ValueError("Exactly one seat must be Hero")
        if not 0 <= dealer_idx < n:
            raise ValueError(f"dealer_idx {dealer_idx} out of range for {n} seats")

        # Rotate Positions[n] so BTN sits at index dealer_idx.
        base_positions = list(Positions[n])
        if dealer_idx:
            base_positions = base_positions[-dealer_idx:] + base_positions[:-dealer_idx]

        seats = tuple(
            Seat(
                name=name, position=base_positions[i], is_hero=is_hero,
                stack=buy_in, hole=(), is_active=True,
                street_bet=0, all_in=False,
            )
            for i, (name, buy_in, is_hero) in enumerate(seat_specs)
        )

        if deck is None:
            rng = rng or np.random.default_rng()
            deck = tuple(int(c) for c in rng.permutation(FULL_DECK))
        else:
            deck = tuple(int(c) for c in deck)
            if len(deck) != 52 or len(set(deck)) != 52:
                raise ValueError("deck must be a permutation of all 52 card IDs")

        sb = small_blind if small_blind is not None else big_blind // 2

        self.state = GameState(
            phase=Phase.WaitingForBlinds,
            seats=seats, to_act_idx=-1,
            board=(), pot=0, street=None,
            current_bet=0, last_aggressor_idx=None, last_raise_increment=0,
            seats_to_act=(), actions=(), decisions=(),
            big_blind=big_blind, small_blind=sb,
            deck=deck, dealer_idx=dealer_idx, winners=(),
        )

    # --------------------------------------------------------
    # Phase transitions
    # --------------------------------------------------------

    def post_blinds(self) -> GameState:
        s = self.state
        if s.phase != Phase.WaitingForBlinds:
            raise InvalidTransition(f"post_blinds() invalid in phase {s.phase}")

        n = len(s.seats)
        # Deal hole cards seat-by-seat: seat[i] gets deck[2i:2i+2].
        # (Round-robin would be more authentic, but seat-by-seat is easier
        # for callers to reason about when constructing deterministic test decks.)
        new_seats = tuple(
            replace(s.seats[i], hole=(s.deck[2 * i], s.deck[2 * i + 1]))
            for i in range(n)
        )
        deck_after_holes = s.deck[2 * n:]

        sb_idx = next(i for i, x in enumerate(new_seats) if x.position == 'SB')
        bb_idx = next(i for i, x in enumerate(new_seats) if x.position == 'BB')

        sb_amt = min(s.small_blind, new_seats[sb_idx].stack)
        new_seats = _replace_seat(
            new_seats, sb_idx,
            stack=new_seats[sb_idx].stack - sb_amt,
            street_bet=sb_amt,
            all_in=(new_seats[sb_idx].stack - sb_amt == 0),
        )
        bb_amt = min(s.big_blind, new_seats[bb_idx].stack)
        new_seats = _replace_seat(
            new_seats, bb_idx,
            stack=new_seats[bb_idx].stack - bb_amt,
            street_bet=bb_amt,
            all_in=(new_seats[bb_idx].stack - bb_amt == 0),
        )

        # Preflop walks UTG -> ... -> BB; BB acts last so they get their option.
        seats_to_act = _full_round_order(new_seats, _first_to_act_preflop(new_seats))

        self.state = replace(
            s, phase=Phase.PreflopBetting, seats=new_seats,
            to_act_idx=seats_to_act[0] if seats_to_act else -1,
            pot=s.pot + sb_amt + bb_amt,
            street='preflop',
            current_bet=bb_amt,
            last_aggressor_idx=bb_idx,        # BB sets the implied opening "raise"
            last_raise_increment=s.big_blind,
            seats_to_act=seats_to_act,
            deck=deck_after_holes,
        )
        return self.state

    def fold(self, name: str) -> GameState:
        return self._betting_action(name, Action.FOLD, 0)

    def check(self, name: str) -> GameState:
        return self._betting_action(name, Action.CHECK, 0)

    def call(self, name: str) -> GameState:
        return self._betting_action(name, Action.CALL, 0)

    def bet(self, name: str, amount: int) -> GameState:
        return self._betting_action(name, Action.BET, amount)

    def raise_to(self, name: str, total: int) -> GameState:
        return self._betting_action(name, Action.RAISE, total)

    def _betting_action(self, name: str, action: Action, amount: int) -> GameState:
        s = self.state
        if s.phase not in BETTING_PHASES:
            raise InvalidTransition(f"{action.value}() invalid in phase {s.phase}")
        idx = _seat_idx(s, name)
        if idx != s.to_act_idx:
            actor = s.seats[s.to_act_idx].name if s.to_act_idx >= 0 else None
            raise InvalidTransition(
                f"It's not {name}'s turn (to_act={actor})"
            )
        seat = s.seats[idx]
        if not seat.is_active:
            raise InvalidTransition(f"{name} is not active in this hand")

        # Apply the specific action and compute the new bet bookkeeping.
        if action == Action.FOLD:
            new_seats = _replace_seat(s.seats, idx, is_active=False)
            new_pot = s.pot
            new_current_bet = s.current_bet
            new_last_aggr = s.last_aggressor_idx
            new_last_raise_inc = s.last_raise_increment
            chips_in = 0
            is_aggressive = False

        elif action == Action.CHECK:
            if seat.street_bet != s.current_bet:
                raise InvalidTransition(
                    f"check() invalid: street_bet={seat.street_bet} != "
                    f"current_bet={s.current_bet}"
                )
            new_seats = s.seats
            new_pot = s.pot
            new_current_bet = s.current_bet
            new_last_aggr = s.last_aggressor_idx
            new_last_raise_inc = s.last_raise_increment
            chips_in = 0
            is_aggressive = False

        elif action == Action.CALL:
            to_call = s.current_bet - seat.street_bet
            if to_call <= 0:
                raise InvalidTransition(
                    f"call() invalid: nothing to call "
                    f"(street_bet={seat.street_bet}, current_bet={s.current_bet})"
                )
            chips_in = min(to_call, seat.stack)
            new_seats = _replace_seat(
                s.seats, idx,
                stack=seat.stack - chips_in,
                street_bet=seat.street_bet + chips_in,
                all_in=(seat.stack - chips_in == 0),
            )
            new_pot = s.pot + chips_in
            new_current_bet = s.current_bet
            new_last_aggr = s.last_aggressor_idx
            new_last_raise_inc = s.last_raise_increment
            is_aggressive = False

        elif action == Action.BET:
            if s.current_bet != 0:
                raise InvalidTransition(
                    f"bet() invalid: current_bet={s.current_bet}; use raise_to()"
                )
            if amount < s.big_blind:
                raise InvalidTransition(
                    f"bet() amount {amount} below min bet (big_blind={s.big_blind})"
                )
            chips_in = min(amount, seat.stack)
            new_seats = _replace_seat(
                s.seats, idx,
                stack=seat.stack - chips_in,
                street_bet=seat.street_bet + chips_in,
                all_in=(seat.stack - chips_in == 0),
            )
            new_pot = s.pot + chips_in
            new_current_bet = chips_in
            new_last_aggr = idx
            new_last_raise_inc = chips_in
            is_aggressive = True

        elif action == Action.RAISE:
            if s.current_bet == 0:
                raise InvalidTransition(
                    "raise_to() invalid: nothing to raise; use bet()"
                )
            min_total = s.current_bet + s.last_raise_increment
            if amount < min_total:
                raise InvalidTransition(
                    f"raise_to() amount {amount} below min-raise {min_total} "
                    f"(current_bet={s.current_bet}, min_inc={s.last_raise_increment})"
                )
            chips_in = min(amount - seat.street_bet, seat.stack)
            new_total = seat.street_bet + chips_in
            new_seats = _replace_seat(
                s.seats, idx,
                stack=seat.stack - chips_in,
                street_bet=new_total,
                all_in=(seat.stack - chips_in == 0),
            )
            new_pot = s.pot + chips_in
            new_last_raise_inc = new_total - s.current_bet
            new_current_bet = new_total
            new_last_aggr = idx
            is_aggressive = True

        else:
            raise InvalidTransition(f"Unknown action {action}")

        # Append to action log.
        new_actions = s.actions + (
            ActionRecord(seat_name=name, action=action, amount=chips_in, phase=s.phase),
        )

        # If Hero acted, record a Decision (math fields stay None until issue #4).
        new_decisions = s.decisions
        if seat.is_hero:
            new_decisions = s.decisions + (
                Decision(
                    seat_name=name, action=action, amount=chips_in, phase=s.phase,
                    pot_at_decision=s.pot,
                    bet_to_call=max(0, s.current_bet - seat.street_bet),
                ),
            )

        # Single survivor: hand ends now, pot to the survivor, no showdown.
        active_count = sum(1 for x in new_seats if x.is_active)
        if active_count == 1:
            winner = next(i for i, x in enumerate(new_seats) if x.is_active)
            new_seats = _replace_seat(
                new_seats, winner,
                stack=new_seats[winner].stack + new_pot,
            )
            self.state = replace(
                s, phase=Phase.HandComplete, seats=new_seats,
                to_act_idx=-1, pot=0,
                current_bet=new_current_bet, last_aggressor_idx=new_last_aggr,
                last_raise_increment=new_last_raise_inc,
                seats_to_act=(), actions=new_actions, decisions=new_decisions,
                winners=(new_seats[winner].name,),
            )
            return self.state

        # Update remaining-to-act queue.
        if is_aggressive:
            seats_to_act = _response_order(new_seats, idx)
        else:
            seats_to_act = tuple(
                i for i in s.seats_to_act
                if i != idx and new_seats[i].is_active and not new_seats[i].all_in
            )

        # Round settled? queue empty AND every still-active non-all-in seat has matched.
        if not seats_to_act and _all_matched(new_seats, new_current_bet):
            return self._settle_betting(
                s, new_seats, new_actions, new_decisions, new_pot,
            )

        next_to_act = seats_to_act[0] if seats_to_act else -1
        self.state = replace(
            s, seats=new_seats, to_act_idx=next_to_act,
            pot=new_pot, current_bet=new_current_bet,
            last_aggressor_idx=new_last_aggr,
            last_raise_increment=new_last_raise_inc,
            seats_to_act=seats_to_act,
            actions=new_actions, decisions=new_decisions,
        )
        return self.state

    def _settle_betting(
        self, s: GameState, new_seats: tuple[Seat, ...],
        new_actions: tuple[ActionRecord, ...],
        new_decisions: tuple[Decision, ...],
        new_pot: int,
    ) -> GameState:
        """Betting just settled — clear per-street state and advance Phase."""
        next_phase = _SETTLE_TARGET[s.phase]
        new_seats = tuple(replace(x, street_bet=0) for x in new_seats)
        self.state = replace(
            s, phase=next_phase, seats=new_seats,
            to_act_idx=-1, pot=new_pot,
            current_bet=0, last_aggressor_idx=None, last_raise_increment=0,
            seats_to_act=(), actions=new_actions, decisions=new_decisions,
        )
        return self.state

    def deal_flop(self) -> GameState:
        return self._deal(Phase.WaitingForFlop, 3, 'flop')

    def deal_turn(self) -> GameState:
        return self._deal(Phase.WaitingForTurn, 1, 'turn')

    def deal_river(self) -> GameState:
        return self._deal(Phase.WaitingForRiver, 1, 'river')

    def _deal(self, expected: Phase, n_cards: int, street: str) -> GameState:
        s = self.state
        if s.phase != expected:
            raise InvalidTransition(f"deal_{street}() invalid in phase {s.phase}")
        if len(s.deck) < n_cards + 1:
            raise InvalidTransition(f"Deck too short to deal {street}")
        # Burn one, then take n_cards.
        new_deck = s.deck[1 + n_cards:]
        new_board = s.board + s.deck[1:1 + n_cards]

        seats_to_act = _full_round_order(s.seats, _first_to_act_postflop(s.seats))
        next_phase = _DEAL_TARGET[expected]

        self.state = replace(
            s, phase=next_phase,
            board=new_board, deck=new_deck, street=street,
            to_act_idx=seats_to_act[0] if seats_to_act else -1,
            current_bet=0, last_aggressor_idx=None, last_raise_increment=0,
            seats_to_act=seats_to_act,
        )

        # Edge case: all remaining seats are all-in. No one can act, so the
        # round trivially settles and we move toward Showdown immediately.
        if not seats_to_act:
            return self._settle_betting(
                self.state, self.state.seats,
                self.state.actions, self.state.decisions, self.state.pot,
            )
        return self.state

    def showdown(self) -> GameState:
        s = self.state
        if s.phase != Phase.Showdown:
            raise InvalidTransition(f"showdown() invalid in phase {s.phase}")

        active = [i for i, x in enumerate(s.seats) if x.is_active]
        # Defensive: a single-survivor hand should already have ended via
        # the betting path, not by reaching Showdown.
        if len(active) < 2:
            winner = active[0]
            new_seats = _replace_seat(
                s.seats, winner,
                stack=s.seats[winner].stack + s.pot,
            )
            self.state = replace(
                s, phase=Phase.HandComplete, seats=new_seats,
                to_act_idx=-1, pot=0, winners=(new_seats[winner].name,),
            )
            return self.state

        # Build (k, 7) hands and score with the vectorized evaluator.
        hands = np.zeros((len(active), 7), dtype=np.int8)
        for k, i in enumerate(active):
            hands[k, :2] = s.seats[i].hole
            hands[k, 2:] = s.board

        scores = evaluate_hands(hands)
        max_score = scores.max()
        winners_local = np.where(scores == max_score)[0]
        winner_seat_idxs = [active[k] for k in winners_local]

        share = s.pot // len(winner_seat_idxs)
        leftover = s.pot % len(winner_seat_idxs)
        new_seats_list = list(s.seats)
        for k, i in enumerate(winner_seat_idxs):
            extra = 1 if k < leftover else 0
            new_seats_list[i] = replace(
                new_seats_list[i],
                stack=new_seats_list[i].stack + share + extra,
            )
        new_seats = tuple(new_seats_list)

        self.state = replace(
            s, phase=Phase.HandComplete, seats=new_seats,
            to_act_idx=-1, pot=0,
            winners=tuple(s.seats[i].name for i in winner_seat_idxs),
        )
        return self.state

    # --------------------------------------------------------
    # Placeholder Villain orchestration (replaced in issue #7)
    # --------------------------------------------------------

    def auto_advance_villains(self) -> GameState:
        """Drive non-Hero seats with a placeholder rule until a Hero decision is needed.

        Rule: fold if facing a bet (street_bet < current_bet), otherwise check.
        Stops when:
        * It's Hero's turn,
        * Phase is non-betting (WaitingFor*, Showdown, HandComplete), or
        * The betting round just settled (no one to act).

        Issue #7 swaps this for the archetype-driven VillainBot.
        """
        # Loop guard: max actions per Hand bounded by O(seats x streets x raises).
        # 1000 is well above any realistic bound and catches infinite-loop bugs.
        for _ in range(1000):
            s = self.state
            if s.phase not in BETTING_PHASES:
                return s
            if s.to_act_idx < 0:
                return s
            seat = s.seats[s.to_act_idx]
            if seat.is_hero:
                return s
            if seat.street_bet < s.current_bet:
                self.fold(seat.name)
            else:
                self.check(seat.name)
        raise InvalidTransition("auto_advance_villains: loop guard tripped")
