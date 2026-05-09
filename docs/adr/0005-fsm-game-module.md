# Game module is a hand-rolled FSM with immutable GameState + ergonomic Game wrapper

The `services/game.py` module is rebuilt from the ground up around an explicit finite-state machine. The design has three components:

1. **A `Phase` enum** with ~10 states: `WaitingForBlinds`, `PreflopBetting`, `WaitingForFlop`, `FlopBetting`, `WaitingForTurn`, `TurnBetting`, `WaitingForRiver`, `RiverBetting`, `Showdown`, `HandComplete`.
2. **An immutable `GameState` dataclass** containing the current `Phase`, board, pot, per-seat data, action history, and decision log. State transitions return a *new* `GameState`.
3. **An ergonomic `Game` class** that wraps `GameState`. Method calls (`game.fold("Hero")`, `game.deal_flop()`) replace `game.state` with the next `GameState`. The class is the imperative shell; the dataclass is the functional core.

The FSM is hand-rolled (not a library like `transitions`). The state space is small enough that a dispatch dict + an `Enum` is clearer than a third-party DSL.

## Considered options

- **Light-touch refactor of existing `game.py`** — rejected. The existing module has no tests, mixes `print()` into business logic, and has no serialization. Building API endpoints on top of it would lock those flaws into the public contract.
- **Hand-rolled coarse FSM (5 streets only)** — rejected. Doesn't enforce "you can't deal the flop while betting is unsettled" as a transition rule; that becomes runtime validation everywhere.
- **`transitions` library, medium granularity** — rejected. The lib's metaprogramming surfaces in tracebacks and adds a dependency for ~80 lines of saved code.
- **Hand-rolled, fine granularity (per-player turn states)** — rejected. State machine becomes harder to hold in your head than the data it's modeling.
- **Pure-functional API (no `Game` class, just `apply_action(state, ...) -> state`)** — rejected. Forces every API call site to write `state = apply_action(state, ...)` boilerplate. Hybrid keeps the data immutable while letting callers use familiar OO syntax.
- **Hand-rolled medium FSM with hybrid `GameState`/`Game`** (chosen).

## Consequences

- The existing `services/game.py` is replaced. There are no existing tests on it to break (only `test_evaluator.py` exists today), so no test-migration cost.
- `GameState` serializes to JSON via `dataclasses.asdict()`. HTTP response schemas wrap that.
- Every API endpoint asserts a precondition on `Phase` before mutating; invalid transitions return HTTP 409.
- The new module captures **Decision** rows as Hero Actions are taken, so that ADR-0007's persistence model has the data it needs.
- Heroes/Villains are still represented by a `Player` class (or equivalent), kept in `GameState`'s seat list.
