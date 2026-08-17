import secrets
from utils.helpers import now
async def create_link(db,owner_id,chat_id,message_id,expires_at=None,usage_limit=0):
    while True:
        token=secrets.token_urlsafe(18)
        try:
            await db.execute("INSERT INTO stored_links VALUES(?,?,?,?,?,?,?,?)",
                (token,owner_id,chat_id,message_id,now(),expires_at,usage_limit,0)); await db.commit(); return token
        except Exception:
            await db.rollback()
