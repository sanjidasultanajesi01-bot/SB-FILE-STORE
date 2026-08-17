from .db import SCHEMA

async def migrate(db):
    await db.executescript(SCHEMA)
    await db.commit()
