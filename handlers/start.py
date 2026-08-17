from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from keyboards.user import main_menu
from keyboards.force_join import join_keyboard
from services.force_join_service import required_channels, check_all
from services.referral_service import process_referral
from utils.helpers import now


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    cfg = context.application.bot_data["cfg"]
    u = update.effective_user
    is_admin = bool(u and u.id in cfg.admin_ids)

    await db.execute(
        "INSERT OR IGNORE INTO users(id,username,first_name,joined_at) VALUES(?,?,?,?)",
        (u.id, u.username, u.first_name, now()))
    await db.execute("UPDATE users SET username=?,first_name=? WHERE id=?", (u.username, u.first_name, u.id))
    await db.commit()

    if await (await db.execute("SELECT banned FROM users WHERE id=?", (u.id,))).fetchone():
        banned_row = await (await db.execute("SELECT banned FROM users WHERE id=?", (u.id,))).fetchone()
        if banned_row and banned_row["banned"]:
            await update.message.reply_text("🚫 <b>ACCESS DENIED</b>\n\nYour account is currently restricted.", parse_mode="HTML")
            return

    if context.args and context.args[0].startswith("ref_"):
        try:
            await process_referral(db, int(context.args[0][4:]), u.id, cfg.referral_reward)
        except (ValueError, TypeError):
            pass

    if not is_admin and not await check_all(context.bot, db, u.id):
        cs = await required_channels(db)
        await update.message.reply_text(
            "🔐 <b>ACCESS LOCKED</b>\n\n"
            "✨ Welcome to the <b>Premium File Store</b>!\n\n"
            "📢 To unlock the store, please join <b>ALL</b> required channels below.\n"
            "👇 Join them one by one, then press the verification button.\n\n"
            "⚠️ <i>Access remains locked until every required channel is verified.</i>",
            parse_mode="HTML", reply_markup=join_keyboard(cs))
        return

    # Never display BOT_TOKEN. Use Telegram's verified bot username instead.
    bot_username = context.application.bot_data.get("bot_username") or "Premium File Store"
    await update.message.reply_text(
        f"🌟 <b>WELCOME, {escape(u.first_name or 'Friend')}!</b> 🌟\n\n"
        f"💎 Welcome to <b>{escape(bot_username)}</b>!\n"
        "🛍️ Browse premium files • 💰 Earn Coins • 🎁 Claim rewards\n"
        "🤝 Refer friends • 📦 Get instant delivery\n\n"
        "👇 <b>Choose an option from the menu below.</b>",
        parse_mode="HTML", reply_markup=main_menu(is_admin=is_admin))
