"""Database seed script skeleton.

Usage:
    cd backend
    python -m scripts.seed

TODO: Add seed data for your models here.
"""

import asyncio

from src.db.session import async_session


async def seed() -> None:
    async with async_session() as session:
        # TODO: Create initial records
        # example = MyModel(name="example")
        # session.add(example)
        # await session.commit()
        print("Seed complete (no data added — update this script).")


if __name__ == "__main__":
    asyncio.run(seed())
