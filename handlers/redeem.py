from telegram.ext import ContextTypes,ConversationHandler
from services.wallet_service import change_balance
from utils.helpers import now
async def redeem_start(update,context):
    await update.message.reply_text("🎟️ Send your redeem code:")
    return 1
async def redeem_code(update,context):
    db=context.application.bot_data["db"]; code=update.message.text.strip().upper(); uid=update.effective_user.id
    await db.execute("BEGIN IMMEDIATE")
    c=await (await db.execute("SELECT * FROM redeem_codes WHERE code=? AND active=1",(code,))).fetchone()
    if not c or (c["usage_limit"] and c["used_count"]>=c["usage_limit"]):
        await db.rollback(); await update.message.reply_text("❌ Invalid or exhausted code."); return ConversationHandler.END
    if await (await db.execute("SELECT 1 FROM redeemed_codes WHERE code=? AND user_id=?",(code,uid))).fetchone():
        await db.rollback(); await update.message.reply_text("❌ You already redeemed this code."); return ConversationHandler.END
    await db.execute("INSERT INTO redeemed_codes VALUES(?,?,?)",(code,uid,now())); await db.execute("UPDATE redeem_codes SET used_count=used_count+1 WHERE code=?",(code,)); await db.commit()
    await change_balance(db,uid,c["amount"],"Redeem",code)
    await update.message.reply_text(f"✅ Redeemed +{c['amount']} Coins.")
    return ConversationHandler.END
