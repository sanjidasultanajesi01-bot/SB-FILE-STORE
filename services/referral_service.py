from utils.helpers import now
from services.wallet_service import change_balance
async def process_referral(db,referrer,referee,reward):
    if referrer==referee: return False
    row=await (await db.execute("SELECT id FROM referrals WHERE referee_id=?",(referee,))).fetchone()
    if row: return False
    if not await (await db.execute("SELECT id FROM users WHERE id=?",(referrer,))).fetchone(): return False
    await db.execute("INSERT INTO referrals VALUES(?,?,?)",(referrer,referee,now()))
    await db.execute("UPDATE users SET referrals=referrals+1,referral_earned=referral_earned+? WHERE id=?",(reward,referrer))
    await db.commit()
    await change_balance(db,referrer,reward,"Referral","Referral reward")
    return True
