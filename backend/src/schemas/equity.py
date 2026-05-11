"""Pydantic schemas for the equity endpoint.

Validates user input at the HTTP boundary so the engine functions can trust
their inputs:
- Card strings match the same `RANK + SUIT` format the engine's `parse_card`
  accepts (e.g. ``"As"``, ``"Th"``, ``"2c"``).
- Hand-type strings are restricted to the canonical 169 hold'em starting
  hands defined in ``engine.variables.handsList``.
- Board lengths are restricted to the legal poker streets: 0 (preflop),
  3 (flop), 4 (turn), 5 (river).
- Hero, board, and ``vs_hand`` cards must be mutually distinct.
- Exactly one of ``vs_hand`` or ``vs_range`` must be supplied.
"""

from collections import Counter
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from src.engine.variables import handsList


# Card string: rank in '23456789TJQKA' followed by suit in 'chds'.
# Mirrors the maps in engine.cards (_RANK_CHARS / _SUIT_CHARS).
CardStr = Annotated[str, StringConstraints(pattern=r"^[23456789TJQKA][chds]$")]
HandTypeStr = Annotated[str, StringConstraints(min_length=2, max_length=3)]

# Hand-type whitelist: one of the 169 canonical starting hands.
_HANDS_SET: frozenset[str] = frozenset(handsList)

# Legal board sizes by street (preflop / flop / turn / river).
_BOARD_LENGTHS: frozenset[int] = frozenset({0, 3, 4, 5})


class EquityRequest(BaseModel):
    """Request body for ``POST /api/equity``.

    Provide exactly one of ``vs_hand`` or ``vs_range``. ``board`` is optional;
    omit it (or send ``null`` / ``[]``) for preflop calls.
    """

    # Hero hole-cards — always exactly 2 cards.
    hero: list[CardStr] = Field(..., min_length=2, max_length=2)

    # Community cards — 0/3/4/5 enforced in the model validator.
    board: list[CardStr] | None = Field(default=None)

    # Single villain hand (2 cards). Mutually exclusive with vs_range.
    vs_hand: list[CardStr] | None = Field(
        default=None, min_length=2, max_length=2,
    )

    # Villain range as a list of canonical hand-type strings (e.g. ['AA', 'AKs']).
    vs_range: list[HandTypeStr] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> "EquityRequest":
        # Exactly one villain spec — XOR check via boolean equality.
        if (self.vs_hand is None) == (self.vs_range is None):
            raise ValueError(
                "Provide exactly one of `vs_hand` or `vs_range`.",
            )

        # Board must be a legal street size.
        board = self.board or []
        if len(board) not in _BOARD_LENGTHS:
            raise ValueError(
                f"`board` must have 0, 3, 4, or 5 cards (got {len(board)}).",
            )

        # Every hand-type string in the range must be one of the 169 canonical
        # types. Catch typos like 'AKx' or 'A-K-s' before they reach the engine.
        if self.vs_range is not None:
            unknown = [h for h in self.vs_range if h not in _HANDS_SET]
            if unknown:
                raise ValueError(f"Unknown hand types: {unknown}")

            # Reject duplicates. Ranges are semantically sets; allowing
            # ['AA', 'AA'] would double-weight that hand type in the
            # aggregate equity calculation because the engine accumulates
            # per list entry. Explicit rejection avoids silent re-weighting.
            dupes = sorted(
                ht for ht, count in Counter(self.vs_range).items()
                if count > 1
            )
            if dupes:
                raise ValueError(
                    f"Duplicate hand types in `vs_range`: {dupes}",
                )

        # No card may appear twice across hero + board + vs_hand.
        all_cards: list[str] = list(self.hero) + list(board)
        if self.vs_hand is not None:
            all_cards += list(self.vs_hand)
        if len(set(all_cards)) != len(all_cards):
            raise ValueError(
                "Duplicate cards in `hero`, `board`, and/or `vs_hand`.",
            )

        return self


class EquityResponse(BaseModel):
    """Response from ``POST /api/equity``.

    ``equity`` is the standard ``win + tie/2`` figure on ``[0, 1]``.

    ``by_hand`` is populated for ``vs_range`` calls only — a per-hand-type
    breakdown of Hero equity against each combo in the villain range. For
    ``vs_hand`` calls it is ``None``.
    """

    equity: float = Field(..., ge=0.0, le=1.0)
    win: float = Field(..., ge=0.0, le=1.0)
    tie: float = Field(..., ge=0.0, le=1.0)
    lose: float = Field(..., ge=0.0, le=1.0)
    by_hand: dict[str, float] | None = None
