"""HTTP surface for the equity calculator.

Single endpoint: ``POST /api/equity``.

Preflop calls (no board) dispatch to the precomputed 169x169 lookup table
in ``engine.preflop_equity.json`` for instant results. Postflop calls run
the vectorized NumPy evaluator — exhaustive on flop/turn/river, where the
remaining-board enumeration is small enough to evaluate every completion.
"""

from fastapi import APIRouter

from src.engine.cards import parse_cards
from src.engine.equity import (
    equity_vs_hand,
    equity_vs_range,
    hand_type_from_cards,
    preflop_equity_lookup,
    preflop_equity_vs_range,
)
from src.schemas.equity import EquityRequest, EquityResponse


router = APIRouter()


@router.post("", response_model=EquityResponse)
async def calculate_equity(req: EquityRequest) -> EquityResponse:
    """Compute Hero equity vs a single Villain hand or a Range.

    The Pydantic schema guarantees:
    - ``hero`` and ``vs_hand`` (when present) are exactly 2 valid cards
    - ``board`` is 0/3/4/5 valid cards
    - exactly one of ``vs_hand`` / ``vs_range`` is supplied
    - all cards are distinct
    """
    board = req.board or []

    if not board:
        # Preflop — short-circuit to the precomputed lookup table.
        # Convert the hero cards to an int8 array so we can read out card IDs.
        hero_arr = parse_cards(req.hero)
        hero_type = hand_type_from_cards(int(hero_arr[0]), int(hero_arr[1]))

        if req.vs_hand is not None:
            villain_arr = parse_cards(req.vs_hand)
            villain_type = hand_type_from_cards(
                int(villain_arr[0]), int(villain_arr[1]),
            )
            result = preflop_equity_lookup(hero_type, villain_type)
        else:
            # vs_range guaranteed non-None by EquityRequest validator.
            result = preflop_equity_vs_range(hero_type, req.vs_range)
    else:
        # Postflop — vectorized evaluator. 3+ cards on the board means the
        # remaining-completion enumeration is small enough to be exhaustive.
        if req.vs_hand is not None:
            result = equity_vs_hand(req.hero, req.vs_hand, board=board)
        else:
            result = equity_vs_range(req.hero, req.vs_range, board=board)

    return EquityResponse(**result)
