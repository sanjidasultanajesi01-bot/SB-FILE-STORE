
from telegram.ext import ContextTypes
from utils.helpers import html_escape

async def referral(update, context):
    cfg = context.application.bot_data["cfg"]
    u = update.effective_user
    username = context.application.bot_data.get("bot_username") or (await context.bot.get_me()).username
    db = context.application.bot_data["db"]
    r = await (await db.execute(
        "SELECT referrals,referral_earned FROM users WHERE id=?", (u.id,)
    )).fetchone()
    referrals = int(r["referrals"] if r else 0)
    earned = int(r["referral_earned"] if r else 0)
    link = f"https://t.me/{username}?start=ref_{u.id}"
    await update.message.reply_text(
        "🤝 <b>REFER & EARN</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Referrals: <b>{referrals}</b>\n"
        f"💰 Total Earned: <b>৳{earned}</b>\n"
        f"🎁 Reward Per Referral: <b>৳{cfg.referral_reward}</b>\n\n"
        f"🔗 <b>Your Referral Link</b>\n<code>{html_escape(link)}</code>",
        parse_mode="HTML")
