"""HTTP surface for the equity calculator.

Single endpoint: ``POST /api/equity``.

Both ``vs_hand`` and ``vs_range`` queries are evaluated against the live
vectorized engine, not the precomputed 169-type lookup table. This preserves
concrete-card information — blockers, suit overlap, and reduced combo counts
all affect the result. The 169-type lookup ignores those effects and was
deemed too lossy at the API boundary; see PR-14 review for the trade-off.

The engine itself selects between exhaustive enumeration and Monte Carlo
based on the number of remaining board cards:
- Postflop (3+ board cards): exhaustive — every completion is evaluated.
- Preflop ``vs_range``: per-combo Monte Carlo at the engine default.
- Preflop ``vs_hand``: 10,000-sample Monte Carlo (avoids the ~1s exhaustive
  enumeration over C(48, 5) board completions).
"""

from fastapi import APIRouter

from src.engine.equity import equity_vs_hand, equity_vs_range
from src.schemas.equity import EquityRequest, EquityResponse


router = APIRouter()

# Preflop vs_hand sample count: 25K gives ~0.3% Monte Carlo precision on
# the equity figure and runs in ~15ms on the vectorized evaluator. Lower
# values (10K) are too noisy to reliably distinguish suit-overlap effects
# in the 1-2% range, which is the whole reason we route through the live
# engine instead of the 169-type lookup.
_PREFLOP_VS_HAND_SAMPLES = 25_000


@router.post("", response_model=EquityResponse)
async def calculate_equity(req: EquityRequest) -> EquityResponse:
    """Compute Hero equity vs a single Villain hand or a Range.

    The Pydantic schema guarantees:
    - ``hero`` and ``vs_hand`` (when present) are exactly 2 valid cards
    - ``board`` is 0/3/4/5 valid cards
    - exactly one of ``vs_hand`` / ``vs_range`` is supplied
    - all cards are distinct
    - ``vs_range`` contains no duplicate hand types
    """
    # Normalize empty/None board to None so the engine's "no board" path
    # is unambiguous (it uses len(board)=0 internally either way).
    board = req.board if req.board else None

    if req.vs_hand is not None:
        # Preflop needs Monte Carlo because exhaustive enumeration over
        # C(48, 5) = 1.7M boards is too slow for an HTTP request. Postflop
        # lets n_samples=None so the engine picks exhaustive automatically.
        n_samples = _PREFLOP_VS_HAND_SAMPLES if board is None else None
        result = equity_vs_hand(
            req.hero, req.vs_hand, board=board, n_samples=n_samples,
        )
    else:
        # equity_vs_range handles street selection internally: per-combo
        # Monte Carlo preflop, exhaustive once the board has 3+ cards.
        result = equity_vs_range(req.hero, req.vs_range, board=board)

    return EquityResponse(**result)
