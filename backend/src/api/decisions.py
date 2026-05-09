"""Unauthenticated calculator endpoints over engine.decisions.

Each endpoint validates input via Pydantic, calls the matching pure-math
function, and returns the computed value plus the inputs (so the client
can render the result without having to track its own request state).
"""

from fastapi import APIRouter

from src.engine.decisions import (
    bet_ev,
    expected_value,
    fold_equity,
    minimum_defense_frequency,
    pot_odds,
    required_equity,
)
from src.schemas.decisions import (
    BetEVRequest,
    BetEVResponse,
    ExpectedValueRequest,
    ExpectedValueResponse,
    FoldEquityRequest,
    FoldEquityResponse,
    MDFRequest,
    MDFResponse,
    PotOddsRequest,
    PotOddsResponse,
    RequiredEquityResponse,
)

router = APIRouter()


@router.post("/pot-odds", response_model=PotOddsResponse)
async def post_pot_odds(body: PotOddsRequest) -> PotOddsResponse:
    return PotOddsResponse(
        pot_odds=pot_odds(body.pot, body.bet_to_call),
        pot=body.pot,
        bet_to_call=body.bet_to_call,
    )


@router.post("/required-equity", response_model=RequiredEquityResponse)
async def post_required_equity(body: PotOddsRequest) -> RequiredEquityResponse:
    return RequiredEquityResponse(
        required_equity=required_equity(body.pot, body.bet_to_call),
        pot=body.pot,
        bet_to_call=body.bet_to_call,
    )


@router.post("/ev", response_model=ExpectedValueResponse)
async def post_ev(body: ExpectedValueRequest) -> ExpectedValueResponse:
    return ExpectedValueResponse(
        expected_value=expected_value(
            equity=body.equity,
            pot=body.pot,
            bet=body.bet,
        ),
        equity=body.equity,
        pot=body.pot,
        bet=body.bet,
    )


@router.post("/bet-ev", response_model=BetEVResponse)
async def post_bet_ev(body: BetEVRequest) -> BetEVResponse:
    return BetEVResponse(
        bet_ev=bet_ev(
            equity=body.equity,
            pot=body.pot,
            bet=body.bet,
            fold_freq=body.fold_freq,
        ),
        equity=body.equity,
        pot=body.pot,
        bet=body.bet,
        fold_freq=body.fold_freq,
    )


@router.post("/fold-equity", response_model=FoldEquityResponse)
async def post_fold_equity(body: FoldEquityRequest) -> FoldEquityResponse:
    return FoldEquityResponse(
        fold_equity=fold_equity(body.pot, body.fold_freq),
        pot=body.pot,
        fold_freq=body.fold_freq,
    )


@router.post("/mdf", response_model=MDFResponse)
async def post_mdf(body: MDFRequest) -> MDFResponse:
    return MDFResponse(
        mdf=minimum_defense_frequency(body.pot, body.bet),
        pot=body.pot,
        bet=body.bet,
    )
