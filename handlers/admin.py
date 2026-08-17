import re
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from keyboards.admin import admin_menu, force_menu, file_menu, payment_menu
from services.payment_service import get_payment_settings, set_payment_setting
from services.wallet_service import change_balance
from utils.helpers import html_escape, now
from telegram.error import Forbidden, BadRequest


def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    cfg = context.application.bot_data["cfg"]
    user = update.effective_user
    return bool(user and user.id in cfg.admin_ids)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    if update.effective_message:
        await update.effective_message.reply_text(
            "👑 <b>ADMIN COMMANDS</b>\n\n"
            "🔐 This panel is visible only to authorized admins.\n"
            "👇 Choose an action below:",
            parse_mode="HTML", reply_markup=admin_menu()
        )


async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open the admin panel from the private ReplyKeyboard button."""
    if not is_admin(update, context):
        return
    await admin(update, context)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    db = context.application.bot_data["db"]

    async def n(sql, params=()):
        row = await (await db.execute(sql, params)).fetchone()
        return int(row["n"] if row else 0)

    users = await n("SELECT COUNT(*) n FROM users")
    active = await n("SELECT COUNT(*) n FROM users WHERE banned=0")
    banned = await n("SELECT COUNT(*) n FROM users WHERE banned=1")
    files = await n("SELECT COUNT(*) n FROM files")
    purchases = await n("SELECT COUNT(*) n FROM purchases")
    pending = await n("SELECT COUNT(*) n FROM payments WHERE status='pending'")
    referrals = await n("SELECT COUNT(*) n FROM referrals")
    rewards = await n("SELECT COUNT(*) n FROM users WHERE reward_count>0")
    coins = await n("SELECT COALESCE(SUM(balance),0) n FROM users")

    await update.effective_message.reply_text(
        "📊 <b>BOT STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{users}</b>\n"
        f"🟢 Active: <b>{active}</b>\n"
        f"🚫 Banned: <b>{banned}</b>\n"
        f"📁 Files: <b>{files}</b>\n"
        f"📦 Purchases: <b>{purchases}</b>\n"
        f"💎 Coins in circulation: <b>{coins}</b>\n"
        f"💳 Pending Payments: <b>{pending}</b>\n"
        f"🤝 Referrals: <b>{referrals}</b>\n"
        f"🎁 Users with rewards: <b>{rewards}</b>",
        parse_mode="HTML", reply_markup=admin_menu()
    )


async def payment_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    db = context.application.bot_data["db"]
    st = await get_payment_settings(db)
    await update.effective_message.reply_text(
        "💳 <b>PAYMENT SETTINGS</b>\n\n"
        f"📱 bKash: <code>{html_escape(st['bkash_number'] or 'Not set')}</code>\n"
        f"📝 Instructions: {html_escape(st['payment_instructions'])}\n\n"
        "Use the buttons below or commands:\n"
        "<code>/setbkash 01XXXXXXXXX</code>\n"
        "<code>/setpaymentinfo Your instructions</code>",
        parse_mode="HTML", reply_markup=payment_menu()
    )


async def setbkash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    value = " ".join(context.args).strip() if context.args else ""
    if not re.fullmatch(r"01\d{9}", value):
        await update.effective_message.reply_text("❌ Usage: /setbkash 01XXXXXXXXX")
        return
    await set_payment_setting(context.application.bot_data["db"], "bkash_number", value)
    await update.effective_message.reply_text("✅ <b>bKash number updated.</b>", parse_mode="HTML")


async def setpaymentinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.effective_message.reply_text("❌ Usage: /setpaymentinfo Your payment instructions")
        return
    await set_payment_setting(context.application.bot_data["db"], "payment_instructions", text)
    await update.effective_message.reply_text("✅ <b>Payment instructions updated.</b>", parse_mode="HTML")


async def addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit() or int(context.args[1]) <= 0:
        await update.effective_message.reply_text("❌ Usage: /addcoins USER_ID AMOUNT")
        return
    uid, amount = int(context.args[0]), int(context.args[1])
    new_balance = await change_balance(context.application.bot_data["db"], uid, amount, "Admin Add", "Admin added Coins")
    await update.effective_message.reply_text("❌ User not found." if new_balance is None else f"✅ Added {amount} Coins. New balance: {new_balance} Coins.")


async def removecoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit() or int(context.args[1]) <= 0:
        await update.effective_message.reply_text("❌ Usage: /removecoins USER_ID AMOUNT")
        return
    uid, amount = int(context.args[0]), int(context.args[1])
    new_balance = await change_balance(context.application.bot_data["db"], uid, -amount, "Admin Remove", "Admin removed Coins")
    await update.effective_message.reply_text("❌ User not found or insufficient balance." if new_balance is None else f"✅ Removed {amount} Coins. New balance: {new_balance} Coins.")


async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    rows = await (await context.application.bot_data["db"].execute("SELECT id,chat_id,title,invite_link,active FROM channels ORDER BY id DESC")).fetchall()
    if not rows:
        await update.effective_message.reply_text("📭 No Force Join channels configured.")
        return
    text = "📢 <b>FORCE JOIN CHANNELS</b>\n\n" + "\n\n".join(
        f"#{r['id']} {'🟢' if r['active'] else '🔴'} {html_escape(r['title'] or r['chat_id'])}\n🆔 <code>{html_escape(r['chat_id'])}</code>\n🔗 {html_escape(r['invite_link'] or 'No link')}"
        for r in rows)
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=force_menu())


async def removechannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("❌ Usage: /removechannel CHANNEL_ID_OR_DB_ID")
        return
    db=context.application.bot_data["db"]
    await db.execute("DELETE FROM channels WHERE id=? OR chat_id=?", (context.args[0], context.args[0]))
    await db.commit()
    await update.effective_message.reply_text("✅ Channel removed if it existed.")


async def addchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    context.user_data["admin_state"] = "add_channel"
    await update.effective_message.reply_text("➕ Send: CHAT_ID | CHANNEL TITLE | INVITE_LINK")


async def addfile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    context.user_data["admin_state"] = "add_file_media"
    await update.effective_message.reply_text("➕ Send the document/photo/video you want to sell.")


async def _file_admin_list(db, limit=30):
    return await (await db.execute(
        "SELECT id,name,price,category,active,purchases,downloads FROM files ORDER BY id DESC LIMIT ?",
        (limit,)
    )).fetchall()

async def delete_file_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update, context):
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.effective_message.reply_text("❌ Usage: /deletefile FILE_ID")
        return
    fid = int(context.args[0])
    db = context.application.bot_data["db"]
    row = await (await db.execute("SELECT id,name FROM files WHERE id=?", (fid,))).fetchone()
    if not row:
        await update.effective_message.reply_text("❌ File not found.")
        return
    # Keep purchase history safe: deactivate first, then remove only if never sold.
    sold = await (await db.execute("SELECT COUNT(*) n FROM purchases WHERE file_id=?", (fid,))).fetchone()
    if int(sold["n"] if sold else 0):
        await db.execute("UPDATE files SET active=0 WHERE id=?", (fid,))
        await db.commit()
        msg = f"🗑️ File <b>{html_escape(row['name'])}</b> was archived because it has purchase history."
    else:
        await db.execute("DELETE FROM files WHERE id=?", (fid,))
        await db.commit()
        msg = f"🗑️ File <b>{html_escape(row['name'])}</b> was permanently deleted."
    await update.effective_message.reply_text(msg, parse_mode="HTML", reply_markup=file_menu())

async def _admin_users(update, context):
    db = context.application.bot_data["db"]
    rows = await (await db.execute(
        "SELECT id,first_name,username,balance,banned FROM users ORDER BY id DESC LIMIT 30"
    )).fetchall()
    if not rows:
        text = "👥 <b>USER MANAGEMENT</b>\n\n📭 No registered users."
    else:
        lines = []
        for r in rows:
            name = html_escape(r["first_name"] or r["username"] or "User")
            status = "🚫" if r["banned"] else "🟢"
            lines.append(f"{status} <code>{r['id']}</code> • {name} • ৳{r['balance']}")
        text = "👥 <b>USER MANAGEMENT</b>\n━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines)
        text += "\n\nUse <code>/ban USER_ID</code> or <code>/unban USER_ID</code>."
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=admin_menu())

async def _admin_logs(update, context):
    db = context.application.bot_data["db"]
    rows = await (await db.execute(
        "SELECT user_id,action,details,created_at FROM logs ORDER BY id DESC LIMIT 20"
    )).fetchall()
    text = "📋 <b>RECENT LOGS</b>\n━━━━━━━━━━━━━━━━━━\n\n"
    text += "\n".join(
        f"• <code>{r['user_id'] or '-'}</code> — <b>{html_escape(r['action'])}</b> — {html_escape(r['details'] or '')}"
        for r in rows
    ) if rows else "📭 No logs yet."
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=admin_menu())

async def ban_user(update, context):
    if not is_admin(update, context): return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.effective_message.reply_text("❌ Usage: /ban USER_ID"); return
    db=context.application.bot_data["db"]
    await db.execute("UPDATE users SET banned=1 WHERE id=?", (int(context.args[0]),)); await db.commit()
    await update.effective_message.reply_text("🚫 User banned.")

async def unban_user(update, context):
    if not is_admin(update, context): return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.effective_message.reply_text("❌ Usage: /unban USER_ID"); return
    db=context.application.bot_data["db"]
    await db.execute("UPDATE users SET banned=0 WHERE id=?", (int(context.args[0]),)); await db.commit()
    await update.effective_message.reply_text("✅ User unbanned.")


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    if q.from_user.id not in context.application.bot_data["cfg"].admin_ids:
        await q.answer("⛔ Admin access required.", show_alert=True)
        return

    await q.answer()
    data = q.data
    db = context.application.bot_data["db"]

    if data in {"admin:home", "admin:menu"}:
        await q.edit_message_text(
            "👑 <b>ADMIN COMMANDS</b>\n\n🔐 Authorized admin panel\n👇 Select an action:",
            parse_mode="HTML", reply_markup=admin_menu())
        return

    if data == "admin:stats":
        await q.edit_message_text("📊 Loading statistics…", parse_mode="HTML")
        await stats(update, context)
        return

    if data == "admin:force":
        await q.edit_message_text("📢 <b>FORCE JOIN MANAGEMENT</b>\n\nChoose an action:", parse_mode="HTML", reply_markup=force_menu())
        return

    if data == "admin:force:add":
        context.user_data["admin_state"] = "add_channel"
        await q.message.reply_text(
            "➕ <b>ADD FORCE-JOIN CHANNEL</b>\n\n"
            "📌 Send <b>only the Channel ID</b>:\n"
            "<code>-1001234567890</code>\n\n"
            "🤖 The bot will automatically fetch the channel title and use its public link or create an invite link when Telegram allows it.\n\n"
            "⚠️ The bot must be an administrator in the channel.",
            parse_mode="HTML")
        return

    if data == "admin:force:list":
        rows = await (await db.execute("SELECT id,chat_id,title,invite_link,active FROM channels ORDER BY id DESC")).fetchall()
        if not rows:
            text = "📭 No force-join channels configured."
        else:
            parts = []
            for r in rows:
                status = "🟢 ON" if r["active"] else "🔴 OFF"
                parts.append(f"#{r['id']} {status}\n📢 {html_escape(r['title'] or r['chat_id'])}\n🆔 <code>{html_escape(r['chat_id'])}</code>")
            text = "📋 <b>FORCE-JOIN CHANNELS</b>\n\n" + "\n\n".join(parts)
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=force_menu())
        return

    if data == "admin:force:remove":
        context.user_data["admin_state"] = "remove_channel"
        await q.message.reply_text("🗑️ Send the channel ID or database channel number to remove.")
        return

    if data == "admin:files":
        await q.edit_message_text("📁 <b>FILE MANAGEMENT</b>\n\nChoose an action:", parse_mode="HTML", reply_markup=file_menu())
        return

    if data == "admin:file:add":
        context.user_data["admin_state"] = "add_file_media"
        await q.message.reply_text("➕ <b>ADD FILE</b>\n\nSend the document/photo/video you want to sell.", parse_mode="HTML")
        return

    if data == "admin:file:list":
        rows = await (await db.execute("SELECT id,name,price,category,active FROM files ORDER BY id DESC LIMIT 30")).fetchall()
        if not rows:
            text = "📭 No files yet."
        else:
            text = "📋 <b>FILES</b>\n\n" + "\n".join(
                f"#{r['id']} {'🟢' if r['active'] else '🔴'} {html_escape(r['name'])} — 💎 {r['price']}"
                for r in rows)
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=file_menu())
        return

    if data == "admin:file:search":
        context.user_data["admin_state"] = "search_file"
        await q.message.reply_text("🔍 Send the file name or keyword to search.")
        return

    if data == "admin:file:delete":
        context.user_data["admin_state"] = "delete_file"
        await q.message.reply_text(
            "🗑️ <b>DELETE FILE</b>\n\nSend the File ID.\n"
            "Example: <code>12</code>\n\n"
            "Files that already have purchases will be archived instead of destroying purchase history.",
            parse_mode="HTML")
        return

    if data == "admin:users":
        await _admin_users(update, context)
        return

    if data == "admin:broadcast":
        from handlers.broadcast import broadcast
        context.user_data["admin_state"] = "broadcast_wait"
        await q.message.reply_text(
            "📣 <b>BROADCAST</b>\n━━━━━━━━━━━━━━━━━━\n\n"
            "Send the message you want to broadcast as your next message.\n"
            "Text, photo, video, document, audio and sticker are supported.\n\n"
            "Use /cancel to stop.",
            parse_mode="HTML")
        return

    if data == "admin:logs":
        await _admin_logs(update, context)
        return

    if data == "admin:settings":
        cfg = context.application.bot_data["cfg"]
        await q.edit_message_text(
            "⚙️ <b>BOT SETTINGS</b>\n━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 Name: <b>{html_escape(cfg.bot_username)}</b>\n"
            f"💰 Daily Reward: <b>৳{cfg.daily_reward}</b>\n"
            f"🤝 Referral Reward: <b>৳{cfg.referral_reward}</b>\n"
            f"🆔 Admin IDs: <code>{html_escape(','.join(map(str, cfg.admin_ids)))}</code>",
            parse_mode="HTML", reply_markup=admin_menu())
        return

    if data == "admin:links":
        rows = await (await db.execute(
            "SELECT token,owner_id,created_at,usage_limit,usage_count FROM stored_links ORDER BY created_at DESC LIMIT 20"
        )).fetchall()
        text = "🔗 <b>STORED LINKS</b>\n━━━━━━━━━━━━━━━━━━\n\n"
        text += "\n".join(
            f"• <code>{html_escape(r['token'])}</code> — owner <code>{r['owner_id']}</code> — {r['usage_count']}/{r['usage_limit'] or '∞'}"
            for r in rows
        ) if rows else "📭 No stored links."
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=admin_menu())
        return

    if data == "admin:redeem":
        context.user_data["admin_state"] = "create_redeem"
        await q.message.reply_text(
            "🎟️ <b>CREATE REDEEM CODE</b>\n\n"
            "Send: <code>CODE | COINS | USAGE_LIMIT</code>\n"
            "Example: <code>SABBIR100 | 100 | 10</code>",
            parse_mode="HTML")
        return

    if data == "admin:support":
        rows = await (await db.execute(
            "SELECT id,user_id,message,status,created_at FROM support_tickets ORDER BY id DESC LIMIT 20"
        )).fetchall()
        text = "🆘 <b>SUPPORT TICKETS</b>\n━━━━━━━━━━━━━━━━━━\n\n"
        text += "\n".join(
            f"#{r['id']} • <code>{r['user_id']}</code> • <b>{html_escape(r['status'])}</b>\n{html_escape(r['message'])}"
            for r in rows
        ) if rows else "📭 No support tickets."
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=admin_menu())
        return

    if data == "admin:coins":
        context.user_data["admin_state"] = "coin_action"
        await q.edit_message_text(
            "💎 <b>COIN MANAGEMENT</b>\n\n"
            "Use commands:\n<code>/addcoins USER_ID AMOUNT</code>\n<code>/removecoins USER_ID AMOUNT</code>\n\n"
            "Or send:\n<code>add USER_ID AMOUNT</code>\n<code>remove USER_ID AMOUNT</code>",
            parse_mode="HTML", reply_markup=admin_menu())
        return

    if data == "admin:payments":
        await q.edit_message_text("💳 <b>PAYMENT MANAGEMENT</b>\n\nChoose an action:", parse_mode="HTML", reply_markup=payment_menu())
        return

    if data == "admin:payments:settings":
        await q.message.reply_text("Use /paymentsettings to view and change bKash/payment instructions.")
        return

    if data == "admin:payments:packages":
        rows = await (await db.execute("SELECT name,coins,price,active FROM payment_packages ORDER BY id")).fetchall()
        text = "💎 <b>COIN PACKAGES</b>\n\n" + ("\n".join(f"{'🟢' if r['active'] else '🔴'} {html_escape(r['name'])}: {r['coins']} Coins — ৳{r['price']}" for r in rows) or "No packages.")
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=payment_menu())
        return



async def admin_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle multi-step admin input created by admin buttons."""
    if not is_admin(update, context):
        return False
    state = context.user_data.get("admin_state")
    if not state or not update.effective_message:
        return False
    db = context.application.bot_data["db"]
    text = (update.effective_message.text or "").strip()

    if state == "add_channel":
        # Only one value is required: channel chat ID (e.g. -1001234567890) or @username.
        chat_id = text.strip()
        if not chat_id:
            await update.effective_message.reply_text("❌ Send only the channel ID, e.g. <code>-1001234567890</code>.", parse_mode="HTML")
            return True
        try:
            chat = await context.bot.get_chat(chat_id)
            me = await context.bot.get_me()
            member = await context.bot.get_chat_member(chat.id, me.id)
            if member.status not in ("administrator", "creator"):
                await update.effective_message.reply_text(
                    "❌ <b>Bot is not an admin.</b>\n\n"
                    "Add the bot as an administrator in that channel, then try again.",
                    parse_mode="HTML"
                )
                return True

            # Public channel: use its public username. Private channel: try creating an invite link.
            invite = getattr(chat, "invite_link", None)
            username = getattr(chat, "username", None)
            if username:
                invite = f"https://t.me/{username}"
            if not invite:
                try:
                    invite_obj = await context.bot.create_chat_invite_link(
                        chat.id, name="Premium File Store Force Join"
                    )
                    invite = invite_obj.invite_link
                except Exception:
                    invite = None

            if not invite:
                await update.effective_message.reply_text(
                    "⚠️ Channel found, but Telegram did not allow an invite link to be created.\n"
                    "Give the bot permission to invite users, or use a public channel.",
                    parse_mode="HTML"
                )
                return True

            title = chat.title or getattr(chat, "full_name", None) or str(chat.id)
            await db.execute(
                """INSERT INTO channels(chat_id,title,invite_link,active)
                   VALUES(?,?,?,1)
                   ON CONFLICT(chat_id) DO UPDATE SET
                   title=excluded.title, invite_link=excluded.invite_link, active=1""",
                (str(chat.id), title, invite)
            )
            await db.commit()
            context.user_data.pop("admin_state", None)
            await update.effective_message.reply_text(
                "✅ <b>Force Join Channel Added!</b>\n\n"
                f"📢 {html_escape(title)}\n"
                f"🆔 <code>{chat.id}</code>\n"
                "🟢 Status: Enabled",
                parse_mode="HTML", reply_markup=admin_menu()
            )
        except Exception as exc:
            await update.effective_message.reply_text(
                "❌ <b>Could not add channel.</b>\n\n"
                "Check that the ID is correct and the bot is an administrator in that channel.",
                parse_mode="HTML"
            )
        return True

    if state == "remove_channel":
        value = text.lstrip("#")
        await db.execute("DELETE FROM channels WHERE id=? OR chat_id=?", (value, value))
        await db.commit()
        context.user_data.pop("admin_state", None)
        await update.effective_message.reply_text("✅ Channel removed (if it existed).", reply_markup=admin_menu())
        return True

    if state == "coin_action":
        parts = text.split()
        if len(parts) == 3 and parts[0].lower() in {"add", "remove"} and parts[1].isdigit() and parts[2].isdigit():
            user_id, amount = int(parts[1]), int(parts[2])
            delta = amount if parts[0].lower() == "add" else -amount
            new_balance = await change_balance(db, user_id, delta, "Admin Add" if delta > 0 else "Admin Remove", f"Admin {parts[0].lower()} coins")
            if new_balance is None:
                await update.effective_message.reply_text("❌ User not found or balance cannot go below zero.")
            else:
                await update.effective_message.reply_text(f"✅ Balance updated. New balance: {new_balance} Coins.")
            context.user_data.pop("admin_state", None)
            return True
        await update.effective_message.reply_text("❌ Use: add USER_ID AMOUNT or remove USER_ID AMOUNT")
        return True

    if state == "delete_file":
        if not text.isdigit():
            await update.effective_message.reply_text("❌ Send only the File ID, e.g. <code>12</code>.", parse_mode="HTML")
            return True
        fid = int(text)
        row = await (await db.execute("SELECT id,name FROM files WHERE id=?", (fid,))).fetchone()
        if not row:
            await update.effective_message.reply_text("❌ File not found.")
            context.user_data.pop("admin_state", None)
            return True
        sold = await (await db.execute("SELECT COUNT(*) n FROM purchases WHERE file_id=?", (fid,))).fetchone()
        if int(sold["n"] if sold else 0):
            await db.execute("UPDATE files SET active=0 WHERE id=?", (fid,))
            msg = "🗃️ File archived because it has purchase history."
        else:
            await db.execute("DELETE FROM files WHERE id=?", (fid,))
            msg = "🗑️ File permanently deleted."
        await db.commit()
        context.user_data.pop("admin_state", None)
        await update.effective_message.reply_text(
            f"✅ <b>{html_escape(row['name'])}</b> — {msg}", parse_mode="HTML", reply_markup=file_menu())
        return True

    if state == "broadcast_wait":
        if update.effective_message and update.effective_message.text == "/cancel":
            context.user_data.pop("admin_state", None)
            await update.effective_message.reply_text("❌ Broadcast cancelled.", reply_markup=admin_menu())
            return True
        from handlers.broadcast import _broadcast_message
        context.user_data.pop("admin_state", None)
        await update.effective_message.reply_text(
            "📣 <b>Broadcast started…</b>\n\nPlease wait while it is delivered.",
            parse_mode="HTML")
        sent, failed, blocked = await _broadcast_message(
            context.bot, db, update.effective_message
        )
        await update.effective_message.reply_text(
            "✅ <b>BROADCAST COMPLETE</b>\n\n"
            f"📨 Sent: <b>{sent}</b>\n"
            f"⚠️ Failed: <b>{failed}</b>\n"
            f"🚫 Blocked/removed: <b>{blocked}</b>",
            parse_mode="HTML", reply_markup=admin_menu())
        return True

    if state == "create_redeem":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 3 or not parts[0] or not parts[1].isdigit() or not parts[2].isdigit() or int(parts[1]) <= 0 or int(parts[2]) <= 0:
            await update.effective_message.reply_text(
                "❌ Format: <code>CODE | COINS | USAGE_LIMIT</code>", parse_mode="HTML")
            return True
        code, amount, limit = parts[0].upper(), int(parts[1]), int(parts[2])
        exists = await (await db.execute("SELECT 1 FROM redeem_codes WHERE code=?", (code,))).fetchone()
        if exists:
            await update.effective_message.reply_text("❌ That code already exists.")
            return True
        await db.execute(
            "INSERT INTO redeem_codes(code,amount,usage_limit,used_count,active) VALUES(?,?,?,0,1)",
            (code, amount, limit)
        )
        await db.commit()
        context.user_data.pop("admin_state", None)
        await update.effective_message.reply_text(
            f"✅ Redeem code created: <code>{html_escape(code)}</code> • +{amount} Coins • {limit} uses",
            parse_mode="HTML", reply_markup=admin_menu())
        return True

    if state == "search_file":
        rows = await (await db.execute("SELECT id,name,price,category,active FROM files WHERE name LIKE ? OR category LIKE ? OR tags LIKE ? ORDER BY id DESC LIMIT 20", (f"%{text}%", f"%{text}%", f"%{text}%"))).fetchall()
        if not rows:
            await update.effective_message.reply_text("📭 No matching files found.")
        else:
            await update.effective_message.reply_text("🔍 <b>SEARCH RESULTS</b>\n\n" + "\n".join(f"#{r['id']} {'🟢' if r['active'] else '🔴'} {html_escape(r['name'])} — 💎 {r['price']}" for r in rows), parse_mode="HTML")
        context.user_data.pop("admin_state", None)
        return True

    if state == "add_file_media":
        media = None
        file_type = None
        if update.effective_message.document:
            media, file_type = update.effective_message.document.file_id, "document"
        elif update.effective_message.photo:
            media, file_type = update.effective_message.photo[-1].file_id, "photo"
        elif update.effective_message.video:
            media, file_type = update.effective_message.video.file_id, "video"
        if not media:
            await update.effective_message.reply_text("❌ Please send a document, photo or video.")
            return True
        context.user_data["pending_file"] = {"file_id": media, "file_type": file_type}
        context.user_data["admin_state"] = "add_file_meta"
        await update.effective_message.reply_text(
            "✅ Media received. Now send:\n\n"
            "<code>Name | Description | Category | Price | Version | Tags</code>\n\n"
            "Example:\n<code>Premium Bot | Full source | Bots | 300 | v2 | python,telegram</code>",
            parse_mode="HTML")
        return True

    if state == "add_file_meta":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 6 or not parts[0] or not parts[3].isdigit() or int(parts[3]) < 0:
            await update.effective_message.reply_text("❌ Format: Name | Description | Category | Price | Version | Tags")
            return True
        p = context.user_data.get("pending_file")
        if not p:
            context.user_data.pop("admin_state", None)
            await update.effective_message.reply_text("❌ File session expired. Start Add File again.")
            return True
        await db.execute("INSERT INTO files(name,description,category,price,file_id,file_type,version,tags,created_at) VALUES(?,?,?,?,?,?,?,?,?)", (parts[0],parts[1],parts[2],int(parts[3]),p["file_id"],p["file_type"],parts[4],parts[5],now()))
        await db.commit()
        context.user_data.pop("admin_state", None)
        context.user_data.pop("pending_file", None)
        await update.effective_message.reply_text("✅ <b>File added successfully.</b>", parse_mode="HTML", reply_markup=admin_menu())
        return True

    return False
