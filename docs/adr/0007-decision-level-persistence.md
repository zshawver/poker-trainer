# Decision-level persistence; no `was_correct` column for now

The persistence schema captures **Decisions** at the granularity of "one row per Hero Action," not just one row per **Hand**. Three tables form the foundation schema:

- `users` — auth identity.
- `completed_hands` — one row per Hand reaching `HandComplete`. Hero hole cards, board, table size, archetypes, full action log (JSONB), pot, winner, created_at.
- `hand_decisions` — one row per Hero Decision within a Hand. Street, equity-at-decision, pot odds, EV of each available Action, the Action the Hero took. Foreign-key to `completed_hands`.

Crucially, `hand_decisions` does **not** include a `was_correct` boolean. Defining what counts as "correct" is a real pedagogical question — pure +EV? Negreanu-flavored GTO? Range-based? — and the user explicitly deferred that question to post-MVP. Capturing the raw math now means we can compute correctness later, against any model, without a migration.

## Why decision-level (and not just hand-level)?

A hand-level row with a JSONB `actions` blob would force every analytics query to parse JSON. Per-decision rows let SQL aggregate over decision counts, EV averages, equity at calling decisions, etc. The user's "see progress over sessions" requirement is decision-level analytics in disguise, and the schema needs to support it cheaply.

## Considered options

- **`completed_hands` only** — rejected. JSONB-only analytics is painful. Forces re-parsing for every report.
- **`completed_hands` + `hand_decisions` with a `was_correct` flag** — rejected for now. Forces a definition of "correct" we don't have.
- **`completed_hands` + `hand_decisions`, no correctness flag** (chosen).
- **Fully normalized (`actions` table per Action, not just per Decision)** — rejected. Captures Villain Actions as rows, which we don't grade. JSONB on `completed_hands` for the full Action log is sufficient.

## Consequences

- Adding correctness scoring later is non-breaking: a `was_correct` column gets added in a future migration, or a `decision_evaluations` table is added for multiple correctness models.
- The frontend's "review this Hand" view reads `completed_hands` + its `hand_decisions` children.
- Aggregate stats (win rate, decisions per session, average EV) are derivable from these tables without further computation tables.
