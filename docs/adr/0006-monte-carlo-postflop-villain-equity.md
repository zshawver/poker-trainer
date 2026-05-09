# Postflop Villain equity uses real Monte Carlo

Villain bots compute postflop equity using `engine.equity.equity_vs_range(hole, vs_range, board=board)`, the same vectorized Monte Carlo function the engine already exposes. The previous heuristic in `villain._estimate_postflop_equity` — preflop-equity lookup plus a `+10%` if a hole card pairs the board and `+5%` if both hole cards are overcards — is **deprecated and removed**.

The reason this is a real ADR rather than a bug-fix patch: the heuristic was a deliberate trade-off when there was no postflop equity function. We now have one, and using it changes Villain behavior fundamentally — bots now fold weak hands on dry boards instead of calling. A future contributor might wonder "why is `_estimate_postflop_equity` so simple?" and re-introduce a fast-but-wrong proxy thinking the slow path was an oversight. This ADR is the answer.

## Why this matters

A trainer's value depends on Villains making realistic decisions. The heuristic gave a Villain holding `7c8c` on `As2h7d` an estimated equity of ~0.40 versus a real value of ~0.15. That Villain calls too loose, raises too loose, and trains the Hero to expect bad opponents.

## Cost

`equity_vs_range` runs in roughly 5–30ms per call with default sample size. A typical postflop Hand has ~10–20 Villain decisions, so total bot-thinking time per Hand is ~50–600ms. Imperceptible in a trainer UI.

## Consequences

- `villain._estimate_postflop_equity` becomes a thin wrapper around `equity_vs_range` (or is deleted entirely if the bot directly calls the engine function).
- New per-archetype tests should cover postflop behavior on canonical board textures (dry, wet, paired, monotone) and assert the bot does the right thing.
- The `bluff_freq` parameter still applies on top of equity-based decisions; it is unaffected.
