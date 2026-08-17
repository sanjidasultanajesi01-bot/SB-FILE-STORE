async def required_channels(db):
    cur=await db.execute("SELECT * FROM channels WHERE active=1"); return await cur.fetchall()
async def is_member(bot,user_id,chat_id):
    try:
        m=await bot.get_chat_member(chat_id,user_id)
        return m.status in ("member","administrator","creator") or (m.status=="restricted" and getattr(m,"is_member",False))
    except Exception: return False
async def check_all(bot,db,user_id):
    return all([await is_member(bot,user_id,c["chat_id"]) for c in await required_channels(db)])
