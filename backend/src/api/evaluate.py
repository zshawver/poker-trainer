"""POST /api/evaluate — wrap the vectorized 7-card hand evaluator."""

from fastapi import APIRouter

from src.engine.cards import parse_cards
from src.engine.evaluator import CATEGORY_SCALE, evaluate_hands
from src.schemas.evaluate import EvaluateRequest, EvaluateResponse

router = APIRouter()

CATEGORY_NAMES: dict[int, str] = {
    1: "high_card",
    2: "pair",
    3: "two_pair",
    4: "three_of_a_kind",
    5: "straight",
    6: "flush",
    7: "full_house",
    8: "four_of_a_kind",
    9: "straight_flush",
    10: "royal_flush",
}


@router.post("", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    # Engine works on (N, 7) int8 arrays; we have N=1.
    hand = parse_cards(req.cards).reshape(1, 7)
    score = int(evaluate_hands(hand)[0])
    category = score // int(CATEGORY_SCALE)
    return EvaluateResponse(
        category=category,
        category_name=CATEGORY_NAMES[category],
        score=score,
    )
