
from datetime import datetime, timedelta, timezone
from telegram.ext import ContextTypes
from services.wallet_service import change_balance
from utils.helpers import now

async def reward(update, context):
    db = context.application.bot_data["db"]
    uid = update.effective_user.id
    r = await (await db.execute("SELECT last_reward FROM users WHERE id=?", (uid,))).fetchone()
    cfg = context.application.bot_data["cfg"]
    if r and r["last_reward"]:
        try:
            if datetime.fromisoformat(r["last_reward"]) + timedelta(hours=24) > datetime.now(timezone.utc):
                await update.message.reply_text(
                    "⏳ <b>DAILY REWARD ALREADY CLAIMED</b>\n\n"
                    "🎁 Come back after 24 hours for your next reward.",
                    parse_mode="HTML")
                return
        except ValueError:
            pass
    await change_balance(db, uid, cfg.daily_reward, "Daily Reward", "Daily reward")
    await db.execute(
        "UPDATE users SET last_reward=?,reward_count=reward_count+1 WHERE id=?",
        (now(), uid)
    )
    await db.commit()
    await update.message.reply_text(
        "🎁 <b>DAILY REWARD CLAIMED!</b>\n\n"
        f"💰 Added: <b>৳{cfg.daily_reward}</b>\n"
        "✨ Your balance has been updated successfully.",
        parse_mode="HTML")
