async def seed_packages(db):
    n=await (await db.execute("SELECT COUNT(*) n FROM payment_packages")).fetchone()
    if n["n"]==0:
        await db.executemany("INSERT INTO payment_packages(name,coins,price) VALUES(?,?,?)",
          [("100 Coins",100,50),("250 Coins",250,100),("500 Coins",500,180),("1000 Coins",1000,350)])
        await db.commit()


async def get_payment_settings(db):
    rows = await (await db.execute(
        "SELECT key,value FROM settings WHERE key IN ('bkash_number','payment_instructions')"
    )).fetchall()
    data = {r["key"]: r["value"] for r in rows}
    return {
        "bkash_number": data.get("bkash_number", ""),
        "payment_instructions": data.get(
            "payment_instructions",
            "Send the payment, then submit your transaction ID and proof."
        ),
    }

async def set_payment_setting(db, key, value):
    if key not in {"bkash_number", "payment_instructions"}:
        raise ValueError("Invalid payment setting")
    await db.execute(
        "INSERT INTO settings(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value)
    )
    await db.commit()
