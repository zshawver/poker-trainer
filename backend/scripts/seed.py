"""Admin CLI for seeding users (no public signup — see ADR-0004).

Usage (from backend/):
    python -m scripts.seed --create-user EMAIL PASSWORD [--admin]
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from src.core.security import hash_password
from src.db.session import async_session
from src.models.user import User


async def create_user(email: str, password: str, is_admin: bool) -> None:
    async with async_session() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"error: a user with email {email!r} already exists", file=sys.stderr)
            sys.exit(1)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_admin=is_admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        admin_tag = " (admin)" if is_admin else ""
        print(f"created user {user.email!r} id={user.id}{admin_tag}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.seed",
        description="Seed users for the poker trainer (admin-only — no public signup).",
    )
    parser.add_argument(
        "--create-user",
        nargs=2,
        metavar=("EMAIL", "PASSWORD"),
        help="create a user with the given email and password",
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="grant admin privileges to the created user",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.create_user is None:
        print("nothing to do — pass --create-user EMAIL PASSWORD", file=sys.stderr)
        sys.exit(2)
    email, password = args.create_user
    asyncio.run(create_user(email, password, args.admin))


if __name__ == "__main__":
    main()
