
from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.helpers import html_escape

async def purchases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    rows = await (await db.execute(
        "SELECT f.id,f.name,f.price FROM purchases p JOIN files f ON f.id=p.file_id "
        "WHERE p.user_id=? ORDER BY p.id DESC",
        (update.effective_user.id,)
    )).fetchall()
    if not rows:
        await update.message.reply_text(
            "📦 <b>MY PURCHASES</b>\n\n"
            "📭 You have not purchased any files yet.\n"
            "🛍️ Visit File Store to explore premium files.",
            parse_mode="HTML")
        return
    buttons = [
        [InlineKeyboardButton(
            f"📄 {str(r['name'])[:45]} • ৳{r['price']}",
            callback_data=f"purchase:get:{r['id']}", style="primary"
        )]
        for r in rows
    ]
    await update.message.reply_text(
        "📦 <b>MY PURCHASES</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📥 Tap a file to download it again:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def redownload(update, context):
    q = update.callback_query
    await q.answer()
    try:
        fid = int(q.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await q.answer("Invalid file.", show_alert=True)
        return
    db = context.application.bot_data["db"]
    row = await (await db.execute(
        "SELECT f.* FROM purchases p JOIN files f ON f.id=p.file_id "
        "WHERE p.user_id=? AND f.id=?",
        (q.from_user.id, fid)
    )).fetchone()
    if not row:
        await q.answer("You do not own this file.", show_alert=True)
        return
    try:
        if row["file_type"] == "document":
            await context.bot.send_document(q.from_user.id, row["file_id"])
        elif row["file_type"] == "photo":
            await context.bot.send_photo(q.from_user.id, row["file_id"])
        elif row["file_type"] == "video":
            await context.bot.send_video(q.from_user.id, row["file_id"])
        else:
            await q.message.reply_text("❌ This media type cannot be re-downloaded automatically.")
            return
        await db.execute("UPDATE files SET downloads=downloads+1 WHERE id=?", (fid,))
        await db.commit()
        await q.answer("📥 File sent.")
    except Exception:
        await q.answer("❌ Delivery failed. Please try again.", show_alert=True)
