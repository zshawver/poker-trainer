"""Request/response schemas for POST /api/evaluate."""

from pydantic import BaseModel, Field, field_validator

_VALID_RANKS = set("23456789TJQKA")
_VALID_SUITS = set("chds")


class EvaluateRequest(BaseModel):
    cards: list[str] = Field(
        ...,
        min_length=7,
        max_length=7,
        description=(
            "Exactly 7 unique cards in two-character form: "
            "rank in '23456789TJQKA' followed by suit in 'chds' (e.g. 'As', 'Th', '2c')."
        ),
        examples=[["As", "Kh", "Qd", "Jc", "Ts", "9s", "8s"]],
    )

    @field_validator("cards")
    @classmethod
    def _validate_cards(cls, value: list[str]) -> list[str]:
        for c in value:
            if (
                len(c) != 2
                or c[0] not in _VALID_RANKS
                or c[1] not in _VALID_SUITS
            ):
                raise ValueError(
                    f"invalid card {c!r}: expected rank in '23456789TJQKA' + suit in 'chds'"
                )
        if len(set(value)) != len(value):
            raise ValueError("cards must be unique")
        return value


class EvaluateResponse(BaseModel):
    category: int = Field(
        ...,
        ge=1,
        le=10,
        description="Hand category 1-10 (1=high card, 10=royal flush).",
    )
    category_name: str = Field(
        ...,
        description="Snake-case category name, e.g. 'royal_flush', 'two_pair'.",
    )
    score: int = Field(
        ...,
        description="Composite score from the evaluator; higher beats lower.",
    )
