# Poker Trainer

A backend that lets a single human (the **Hero**) play hands of no-limit Texas hold'em against archetype-driven bots (**Villains**) for the purpose of training real-money decision quality. The trainer captures every **Decision** with its math context (equity, pot odds, EV) so the human can review what they did and — eventually — be scored against a correctness model.

## Language

### People at the table

**Hero**:
The human user being trained. Exactly one Hero per Game.
_Avoid_: Player (ambiguous), User (means the auth-layer concept).

**Villain**:
A non-Hero seat at the table, controlled by a bot.
_Avoid_: Opponent, NPC, AI.

**User**:
The auth-layer identity that owns a session. A User has exactly one Hero in any given Game; multi-tabling is out of scope.
_Avoid_: Player, Account.

### Game and time structure

**Game**:
A sit-down session at the table — a configured set of seats, archetypes, blinds, and buy-ins. A Game contains many Hands and outlives any single Hand.
_Avoid_: Session (means the auth/login concept), Match, Round.

**Hand**:
One deal from blinds posted to showdown (or last-player-standing). The atomic unit of training. A Hand contains 1–4 Streets.
_Avoid_: Round, Deal.

**HandState** (or **GameState** in code):
The full snapshot of an in-progress Hand: phase, board, pot, per-seat stacks/holes/bets, action history. Lives in process memory while the Hand is active; not persisted (per ADR-0002).

**Street**:
A betting round within a Hand. Exactly one of: `preflop`, `flop`, `turn`, `river`.
_Avoid_: Round, Phase.

**Phase** (FSM state):
A discrete state of the FSM that drives a Hand: `WaitingForBlinds`, `PreflopBetting`, `WaitingForFlop`, `FlopBetting`, `WaitingForTurn`, `TurnBetting`, `WaitingForRiver`, `RiverBetting`, `Showdown`, `HandComplete`. Distinct from Street: a single Street can be entered, bet through, and exited via two Phases.
_Avoid_: State (overloaded), Stage.

### Action and decision

**Action**:
A single move a seat makes in a Phase. Exactly one of: `fold`, `check`, `call`, `bet`, `raise`. Posts of `sb`/`bb` are blinds, not Actions.
_Avoid_: Move, Play.

**Decision**:
A moment where the **Hero** faces a choice with money at stake. One Decision per Hero Action. A Decision is recorded with its math context (equity, pot odds, EV of available options) at the instant it is made — see ADR-0007.
_Avoid_: Choice, Move (Move ≈ Action; Decision is Hero-specific and carries math).

**Showdown**:
The terminal Phase where surviving seats reveal hole cards and the pot is awarded by hand strength. Skipped when only one seat remains pre-river.

### Math vocabulary

**Equity**:
Probability of winning the pot at showdown given currently-known cards. Computed as `(wins + ties/2) / total`. Always a value in `[0, 1]`.

**Range**:
A set of starting hand types one player is assumed to hold. Encoded as a list of strings (`['AA', 'KK', ..., 'AKs']`). Position-dependent for Villains via `engine/ranges.py`.

**Hand type**:
A starting-hand class string: rank-pair (`AA`), suited (`AKs`), or offsuit (`AKo`). 169 distinct types in hold'em.
_Avoid_: Holding (ambiguous), Hand (overloaded with the time-unit).

**Pot odds**:
The fraction `bet_to_call / (pot + bet_to_call)`. Equal to the minimum equity at which calling breaks even.

**Required equity**:
Synonym for pot odds, framed as a threshold the Hero must beat to make a +EV call. Used in trainer prompts ("Your required equity is 28% — do you call?").

**EV** (expected value):
The chip-denominated profit/loss expected from an Action over many trials, given equity and assumed Villain frequencies. Always reported in chips, never in big blinds, in the foundation.

**Fold equity**:
The portion of total EV from an aggressive Action that comes from Villain folding (vs. the equity-when-called portion). Quantified as `villain_fold_freq * pot`.

**MDF** (minimum defense frequency):
The minimum frequency at which a player must continue (call or raise) facing a bet to make their opponent's bluffs unprofitable. Computed as `pot / (pot + bet)`.

### Archetypes and ranges

**Archetype**:
A villain personality defined by a fixed dictionary of behavioral parameters (range tightness, betting thresholds, bluff frequency, noise). One of: `TAG`, `LAG`, `NIT`, `CALLING_STATION`, `MANIAC`.
_Avoid_: Profile, Persona, Style.

**Position**:
A seat's relative-to-button label: `UTG`, `MP`, `CO`, `BTN`, `SB`, `BB` (and HJ/UTG+1/etc. at larger tables). Determines opening Range and acting order.

**Opening range**:
The set of Hand types a position will voluntarily open-raise with when folded to. Defined per (table_size, position) in `engine/ranges.py`.

## Relationships

- A **User** owns one or more **Games**.
- A **Game** has one **Hero** (the User) and 2–8 **Villains** (bots).
- A **Game** contains many **Hands**, played sequentially.
- A **Hand** progresses through 1–4 **Streets**, each entered and exited via the FSM **Phases**.
- A **Hand** records many **Actions** (one per seat per Phase) and many **Decisions** (one per Hero Action).
- An **Action** has no math context; a **Decision** wraps a Hero Action with its **Equity**, **Pot odds**, and **EV** at decision time.
- A **Villain** has exactly one **Archetype**.
- An **Archetype** does not change mid-Game (drift/tilt is post-MVP).

## Example dialogue

> **Trainer designer:** "When the **Hero** raises preflop and a **Villain** 3-bets, do we record both moves as **Decisions**?"
>
> **Domain expert:** "No — only the Hero's response is a **Decision**. The Villain's 3-bet is just an **Action**. The trainer doesn't grade Villains; the only thing we capture math for is what the Hero did, because that's what we're training."

> **Trainer designer:** "If the Hero folds preflop, do we record a **Decision**?"
>
> **Domain expert:** "Yes. Fold is an **Action**; therefore the Hero faced a **Decision**. We record the **Equity** of their folded hand vs the raiser's **Range** and the **Pot odds** they were getting — even if they didn't call, the math they walked away from is what we're training them to read."

> **Trainer designer:** "What about a **Hand** where the Hero is in the BB and gets to **check** preflop?"
>
> **Domain expert:** "Check is an **Action** but the Hero faced no real choice — `bet_to_call` was 0. We still record it as a **Decision** for completeness; **Pot odds** and **EV** of folding are degenerate, and the analytics layer can filter these out."

## Flagged ambiguities

- **Session**: never used in domain language. The auth concept is **User session**; the time-at-the-table concept is **Game**. Don't say "training session" — say **Game**.
- **Round**: ambiguous between **Hand** (one deal) and **Street** (one betting round within a Hand). Don't use it; pick the precise term.
- **Player**: ambiguous between **Hero**, **Villain**, and a generic "any seat at the table" sense. The code uses `Player` as a class for any seat, but in domain prose use **Hero** or **Villain**.
- **State**: ambiguous between **Phase** (FSM state) and **HandState** (the full snapshot). Use **Phase** for the FSM enum; use **HandState** for the snapshot.
- **GTO-correct**: deliberately not yet defined. ADR-0007 defers the question of what counts as a "correct" Decision. Don't put `was_correct` semantics into code or docs until that is grilled out.
