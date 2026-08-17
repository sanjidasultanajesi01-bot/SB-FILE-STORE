from telegram import Update
from telegram.ext import ContextTypes
from keyboards.user import main_menu
from keyboards.force_join import join_keyboard
from services.force_join_service import required_channels, check_all


async def fj_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    db = context.application.bot_data["db"]
    is_admin = q.from_user.id in context.application.bot_data["cfg"].admin_ids
    if is_admin or await check_all(context.bot, db, q.from_user.id):
        await q.message.edit_text("✅ <b>Access unlocked!</b>", parse_mode="HTML")
        await q.message.reply_text("🌟 Welcome! Choose an option below.", reply_markup=main_menu(is_admin=is_admin))
    else:
        await q.answer("❌ You have not joined every required channel.", show_alert=True)
