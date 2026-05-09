# Multi-user with invite-only auth; no public signup

The auth model is a real `User` table with JWT-protected endpoints, but **there is no public signup endpoint**. New Users are created by an admin (initially, by running `scripts/seed.py` against the database). This means the trainer can be safely deployed to a public URL without becoming a free service for the entire internet.

Sharing with poker buddies is a deliberate, manual act: the admin runs a CLI command (or, post-foundation, hits an admin-only HTTP endpoint) to create the buddy's account.

## Considered options

- **No auth** — rejected. The user wants to share the trainer with others later, and retrofitting auth onto an unauthenticated app is more work than building it in.
- **Single-user, no `User` table** — rejected for the same reason.
- **Invite-only multi-user** (chosen).
- **Public signup with email verification** — rejected. Out of scope for MVP; adds email infrastructure, password-reset flow, rate limiting.

## Consequences

- The `User` model is the first concrete model in the codebase. Foreign keys from `completed_hands` and `hand_decisions` reference `users.id`.
- `src/api/auth.py` `login` endpoint is wired to the DB; `src/core/deps.py` `get_current_user` does a real lookup.
- No `POST /api/auth/signup` endpoint exists. Adding one later is a one-file change but should be a deliberate decision (likely a follow-up ADR).
- Admin user creation is documented in the README as `python -m scripts.seed --create-user <email> <password>`.
