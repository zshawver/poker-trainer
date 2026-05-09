"""
Pure-math decision helpers used by the trainer to score Hero choices.

Every function maps directly to a vocabulary entry in CONTEXT.md
("Math vocabulary" section): pot odds, required equity, EV, fold equity,
and minimum defense frequency. All inputs and outputs are chip-denominated
floats; equity and frequency arguments are in [0, 1].

These functions are stateless — no DB, no I/O, no NumPy. They are intended
to be called per-Decision (one Hero Action) and exposed individually via
/api/decisions/* for client-side calculator widgets.
"""


def pot_odds(pot: float, bet_to_call: float) -> float:
    """Fraction of the next pot the Hero must contribute to call.

    Defined in CONTEXT.md as `bet_to_call / (pot + bet_to_call)`. Equal
    to the minimum equity at which calling breaks even.

    Parameters
    ----------
    pot : float
        Chips already in the pot, including any Villain bet being called.
    bet_to_call : float
        Chips the Hero must add to continue.

    Returns
    -------
    float
        Pot odds in [0, 1]. Returns 0.0 when `bet_to_call` is 0 (no
        equity required when there is nothing to call).
    """
    if bet_to_call == 0:
        return 0.0
    return bet_to_call / (pot + bet_to_call)


def required_equity(pot: float, bet_to_call: float) -> float:
    """Minimum equity the Hero needs to make a +EV call.

    Synonym for `pot_odds` per CONTEXT.md — kept as a separate symbol so
    trainer prompts can use either name ("Your pot odds are 33%" vs
    "Your required equity is 33%"). Delegates to `pot_odds` so there is
    one source of truth for the math.
    """
    return pot_odds(pot, bet_to_call)


def expected_value(
    equity: float,
    pot: float,
    bet: float,
    fold_freq: float = 0.0,
) -> float:
    """EV in chips of betting `bet` into `pot` with given fold equity.

    Models an aggressive Action: Villain folds with probability
    `fold_freq` (winning the existing pot) or calls and goes to showdown
    where the Hero realizes `equity` of the called pot.

        EV = fold_freq * pot
           + (1 - fold_freq) * (equity * (pot + 2*bet) - bet)

    For a pure call, pass `fold_freq=0.0`; the formula reduces to the
    standard call EV `equity * (pot + 2*bet) - bet`.

    Parameters
    ----------
    equity : float
        Hero's equity at showdown when called, in [0, 1].
    pot : float
        Chips in the pot before the Hero's action.
    bet : float
        Chips the Hero puts in.
    fold_freq : float, default 0.0
        Probability Villain folds to the action, in [0, 1].

    Returns
    -------
    float
        Expected chip profit/loss of the action.
    """
    ev_when_called = equity * (pot + 2 * bet) - bet
    return fold_freq * pot + (1 - fold_freq) * ev_when_called


def fold_equity(pot: float, fold_freq: float) -> float:
    """Chips of EV that come from Villain folding to a bet.

    Defined in CONTEXT.md as `villain_fold_freq * pot` — the portion of
    total EV from an aggressive Action attributable to the fold, before
    accounting for showdown equity when called.

    Parameters
    ----------
    pot : float
        Chips in the pot before the Hero's action.
    fold_freq : float
        Probability Villain folds to the action, in [0, 1].

    Returns
    -------
    float
        Fold-equity contribution, in chips.
    """
    return fold_freq * pot


def minimum_defense_frequency(pot: float, bet: float) -> float:
    """Frequency the Hero must continue to make a Villain bluff break even.

    Defined in CONTEXT.md as `pot / (pot + bet)`. A defending player who
    folds more often than `1 - mdf` lets pure bluffs profit.

    Parameters
    ----------
    pot : float
        Chips in the pot before the Villain's bet.
    bet : float
        Chips Villain bet.

    Returns
    -------
    float
        MDF in [0, 1]. Returns 0.0 when `bet` is 0 (no bet faced, no
        defense required).
    """
    if bet == 0:
        return 0.0
    return pot / (pot + bet)
