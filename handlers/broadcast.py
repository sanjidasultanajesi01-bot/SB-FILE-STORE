import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest

log = logging.getLogger(__name__)

async def _send_copy(bot, target_id, source_chat_id, source_message_id):
    return await bot.copy_message(
        chat_id=target_id,
        from_chat_id=source_chat_id,
        message_id=source_message_id,
    )

async def _broadcast_message(bot, db, source_message):
    rows = await (await db.execute(
        "SELECT id FROM users WHERE banned=0 ORDER BY id"
    )).fetchall()
    sent = failed = blocked = 0

    for row in rows:
        uid = int(row["id"])
        try:
            await _send_copy(bot, uid, source_message.chat_id, source_message.message_id)
            sent += 1
        except Forbidden:
            blocked += 1
            await db.execute("UPDATE users SET banned=1 WHERE id=?", (uid,))
        except (BadRequest, Exception) as exc:
            # BadRequest includes deleted/invalid users; don't stop the whole broadcast.
            failed += 1
            log.debug("Broadcast failed for %s: %s", uid, exc)
        await asyncio.sleep(0.05)

    await db.commit()
    return sent, failed, blocked

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = context.application.bot_data["cfg"]
    if update.effective_user.id not in cfg.admin_ids:
        return

    # /broadcast used as a reply to any message = immediate broadcast.
    if update.effective_message.reply_to_message:
        await update.effective_message.reply_text(
            "📣 <b>Broadcast started…</b>\n\n"
            "The message is being delivered to registered users.",
            parse_mode="HTML"
        )
        sent, failed, blocked = await _broadcast_message(
            context.bot, context.application.bot_data["db"],
            update.effective_message.reply_to_message
        )
        await update.effective_message.reply_text(
            "✅ <b>BROADCAST COMPLETE</b>\n\n"
            f"📨 Sent: <b>{sent}</b>\n"
            f"⚠️ Failed: <b>{failed}</b>\n"
            f"🚫 Blocked/removed: <b>{blocked}</b>",
            parse_mode="HTML"
        )
        return

    context.user_data["admin_state"] = "broadcast_wait"
    await update.effective_message.reply_text(
        "📣 <b>BROADCAST</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Send the message you want to broadcast now.\n"
        "You can send text, photo, video, document, audio, sticker, etc.\n\n"
        "⚠️ Send it as the next message; it will be copied to all active users.\n"
        "Use /cancel to stop.",
        parse_mode="HTML"
    )

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await broadcast(update, context)
