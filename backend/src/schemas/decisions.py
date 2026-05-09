"""Pydantic schemas for /api/decisions/* request/response bodies.

Each response echoes the input fields back so the client can render a
calculator widget without having to remember what it just sent.
"""

from pydantic import BaseModel, Field


# ========== Pot odds / required equity (shared shape) ==========


class PotOddsRequest(BaseModel):
    pot: float = Field(ge=0, description="Chips already in the pot, including the Villain bet being called.")
    bet_to_call: float = Field(ge=0, description="Chips the Hero must add to continue.")


class PotOddsResponse(BaseModel):
    pot_odds: float
    pot: float
    bet_to_call: float


class RequiredEquityResponse(BaseModel):
    required_equity: float
    pot: float
    bet_to_call: float


# ========== Expected value (call EV) ==========


class ExpectedValueRequest(BaseModel):
    equity: float = Field(ge=0, le=1, description="Hero's equity at showdown.")
    pot: float = Field(ge=0, description="Displayed pot (includes Villain's bet being called).")
    bet: float = Field(ge=0, description="Chips Hero must add to call.")


class ExpectedValueResponse(BaseModel):
    expected_value: float
    equity: float
    pot: float
    bet: float


# ========== Bet/raise EV (with fold equity) ==========


class BetEVRequest(BaseModel):
    equity: float = Field(ge=0, le=1, description="Hero's equity at showdown when called.")
    pot: float = Field(ge=0, description="Displayed pot before Hero's bet/raise.")
    bet: float = Field(ge=0, description="Chips Hero adds (raise amount above any Villain bet).")
    fold_freq: float = Field(default=0.0, ge=0, le=1, description="Probability Villain folds to the action.")


class BetEVResponse(BaseModel):
    bet_ev: float
    equity: float
    pot: float
    bet: float
    fold_freq: float


# ========== Fold equity ==========


class FoldEquityRequest(BaseModel):
    pot: float = Field(ge=0)
    fold_freq: float = Field(ge=0, le=1)


class FoldEquityResponse(BaseModel):
    fold_equity: float
    pot: float
    fold_freq: float


# ========== Minimum defense frequency ==========


class MDFRequest(BaseModel):
    pot: float = Field(ge=0, description="Chips in the pot before the Villain's bet.")
    bet: float = Field(ge=0, description="Chips Villain bet.")


class MDFResponse(BaseModel):
    mdf: float
    pot: float
    bet: float
