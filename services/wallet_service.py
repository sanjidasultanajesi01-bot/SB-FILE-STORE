from utils.helpers import now
async def change_balance(db,user_id,amount,kind,description):
    await db.execute("BEGIN IMMEDIATE")
    row=await (await db.execute("SELECT balance FROM users WHERE id=?",(user_id,))).fetchone()
    if not row or row["balance"]+amount<0:
        await db.rollback(); return None
    new=row["balance"]+amount
    await db.execute("UPDATE users SET balance=? WHERE id=?",(new,user_id))
    await db.execute("INSERT INTO transactions(user_id,amount,kind,description,created_at,balance_after) VALUES(?,?,?,?,?,?)",
                     (user_id,amount,kind,description,now(),new))
    await db.commit(); return new
