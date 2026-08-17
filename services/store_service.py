
from utils.helpers import now

async def purchase(db, user_id, file_id):
    await db.execute("BEGIN IMMEDIATE")
    try:
        f = await (await db.execute(
            "SELECT * FROM files WHERE id=? AND active=1", (file_id,)
        )).fetchone()
        u = await (await db.execute(
            "SELECT balance FROM users WHERE id=?", (user_id,)
        )).fetchone()
        if not f or not u:
            await db.rollback()
            return None, "not_found"
        exists = await (await db.execute(
            "SELECT id FROM purchases WHERE user_id=? AND file_id=?", (user_id, file_id)
        )).fetchone()
        if exists:
            await db.rollback()
            return f, "owned"
        price = int(f["price"])
        balance = int(u["balance"])
        if balance < price:
            await db.rollback()
            return f, "insufficient"
        new_balance = balance - price
        await db.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user_id))
        await db.execute(
            "INSERT INTO purchases(user_id,file_id,created_at) VALUES(?,?,?)",
            (user_id, file_id, now())
        )
        await db.execute(
            "UPDATE files SET purchases=purchases+1 WHERE id=?", (file_id,)
        )
        await db.execute(
            "INSERT INTO transactions(user_id,amount,kind,description,created_at,balance_after) VALUES(?,?,?,?,?,?)",
            (user_id, -price, "Purchase", f["name"], now(), new_balance)
        )
        await db.commit()
        return f, "ok"
    except Exception:
        await db.rollback()
        raise
