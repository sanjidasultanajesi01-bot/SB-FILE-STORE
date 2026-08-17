
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.store import file_list_keyboard, category_keyboard, file_detail_keyboard, purchase_confirm_keyboard
from utils.helpers import html_escape

PAGE_SIZE = 7

async def _rows(db, category=None, page=0):
    offset = max(0, page) * PAGE_SIZE
    if category:
        total_row = await (await db.execute(
            "SELECT COUNT(*) n FROM files WHERE active=1 AND category=?", (category,)
        )).fetchone()
        rows = await (await db.execute(
            "SELECT * FROM files WHERE active=1 AND category=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (category, PAGE_SIZE, offset)
        )).fetchall()
    else:
        total_row = await (await db.execute(
            "SELECT COUNT(*) n FROM files WHERE active=1"
        )).fetchone()
        rows = await (await db.execute(
            "SELECT * FROM files WHERE active=1 ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE, offset)
        )).fetchall()
    total = int(total_row["n"] if total_row else 0)
    return rows, total

async def render_store(message, context, page=0, category=None):
    db = context.application.bot_data["db"]
    rows, total = await _rows(db, category, page)
    if not rows and page > 0:
        page = 0
        rows, total = await _rows(db, category, page)

    if category:
        title = f"📂 <b>{html_escape(category)}</b>"
    else:
        title = "🛍️ <b>PREMIUM FILE STORE</b>"

    if not rows:
        text = (
            f"{title}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📭 <b>No files available right now.</b>\n"
            "✨ New premium files will appear here soon."
        )
    else:
        text = (
            f"{title}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 <b>Select a file to view its full description:</b>\n\n"
            f"📦 Showing {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + len(rows)} of {total}\n"
            "💰 Price is shown in Bangladeshi Taka."
        )
    await message.reply_text(
        text, parse_mode="HTML",
        reply_markup=file_list_keyboard(
            rows, page, page > 0, (page + 1) * PAGE_SIZE < total
        )
    )

async def store(update, context):
    await render_store(update.effective_message, context, 0)

async def details(update, context):
    q = update.callback_query
    await q.answer()
    try:
        fid = int(q.data.split(":")[1])
    except (ValueError, IndexError):
        await q.answer("Invalid file.", show_alert=True)
        return
    db = context.application.bot_data["db"]
    f = await (await db.execute(
        "SELECT * FROM files WHERE id=? AND active=1", (fid,)
    )).fetchone()
    if not f:
        await q.answer("This file is no longer available.", show_alert=True)
        return
    text = (
        "📄 <b>FILE DETAILS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>{html_escape(f['name'])}</b>\n\n"
        f"📝 <b>Description:</b>\n{html_escape(f['description'] or 'No description provided.')}\n\n"
        f"📂 <b>Category:</b> {html_escape(f['category'] or 'General')}\n"
        f"🏷️ <b>Tags:</b> {html_escape(f['tags'] or '—')}\n"
        f"🔖 <b>Version:</b> {html_escape(f['version'] or 'Latest')}\n"
        f"💰 <b>Price:</b> ৳{f['price']}\n\n"
        "👇 <b>Choose an option:</b>"
    )
    try:
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=file_detail_keyboard(fid))
    except Exception:
        await q.message.reply_text(text, parse_mode="HTML", reply_markup=file_detail_keyboard(fid))

async def buy(update, context):
    q = update.callback_query
    await q.answer()
    try:
        fid = int(q.data.split(":")[1])
    except (ValueError, IndexError):
        await q.answer("Invalid file.", show_alert=True)
        return
    db = context.application.bot_data["db"]
    f = await (await db.execute("SELECT * FROM files WHERE id=? AND active=1", (fid,))).fetchone()
    if not f:
        await q.answer("File unavailable.", show_alert=True)
        return
    u = await (await db.execute("SELECT balance FROM users WHERE id=?", (q.from_user.id,))).fetchone()
    balance = int(u["balance"] if u else 0)
    if balance < int(f["price"]):
        await q.message.reply_text(
            "❌ <b>INSUFFICIENT BALANCE</b>\n\n"
            f"💰 Your Balance: <b>৳{balance}</b>\n"
            f"💳 Required: <b>৳{f['price']}</b>\n\n"
            "Use <b>My Wallet</b> to add balance.",
            parse_mode="HTML"
        )
        return
    await q.message.reply_text(
        "📦 <b>PURCHASE CONFIRMATION</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📄 File: <b>{html_escape(f['name'])}</b>\n"
        f"💰 Price: <b>৳{f['price']}</b>\n"
        f"💳 Your Balance: <b>৳{balance}</b>\n\n"
        "⚠️ Confirm only if you want to purchase this file.",
        parse_mode="HTML",
        reply_markup=purchase_confirm_keyboard(fid)
    )

async def confirm_purchase(update, context):
    q = update.callback_query
    await q.answer()
    try:
        fid = int(q.data.split(":")[1])
    except (ValueError, IndexError):
        await q.answer("Invalid file.", show_alert=True)
        return
    db = context.application.bot_data["db"]
    from services.store_service import purchase
    f, status = await purchase(db, q.from_user.id, fid)
    if status == "owned":
        await q.message.reply_text("📦 <b>Already purchased.</b>\n📥 Use My Purchases to download it again.", parse_mode="HTML")
        return
    if status == "insufficient":
        await q.message.reply_text("❌ <b>Insufficient balance.</b>\nPlease add balance and try again.", parse_mode="HTML")
        return
    if status != "ok" or not f:
        await q.message.reply_text("❌ Purchase could not be completed. Nothing was charged.", parse_mode="HTML")
        return
    try:
        if f["file_type"] == "document":
            await context.bot.send_document(q.from_user.id, f["file_id"],
                caption=f"🎉 <b>Purchase Delivered!</b>\n\n📄 {html_escape(f['name'])}\n💰 ৳{f['price']}",
                parse_mode="HTML")
        elif f["file_type"] == "photo":
            await context.bot.send_photo(q.from_user.id, f["file_id"],
                caption=f"🎉 <b>Purchase Delivered!</b>\n\n📄 {html_escape(f['name'])}\n💰 ৳{f['price']}",
                parse_mode="HTML")
        elif f["file_type"] == "video":
            await context.bot.send_video(q.from_user.id, f["file_id"],
                caption=f"🎉 <b>Purchase Delivered!</b>\n\n📄 {html_escape(f['name'])}\n💰 ৳{f['price']}",
                parse_mode="HTML")
        else:
            await context.bot.copy_message(q.from_user.id, q.message.chat_id, int(f["message_id"]))
        await db.execute("UPDATE files SET downloads=downloads+1 WHERE id=?", (f["id"],))
        await db.commit()
    except Exception:
        from services.wallet_service import change_balance
        await change_balance(db, q.from_user.id, int(f["price"]), "Refund", "Automatic refund after delivery failure")
        await q.message.reply_text(
            "⚠️ <b>DELIVERY FAILED</b>\n\n"
            "💰 Your balance has been automatically refunded.\n"
            "🙏 Please contact support if this continues.",
            parse_mode="HTML"
        )

async def store_callback(update, context):
    q = update.callback_query
    data = q.data
    if data.startswith("store:page:"):
        await q.answer()
        try:
            page = int(data.rsplit(":", 1)[1])
        except ValueError:
            return
        await render_store(q.message, context, page)
    elif data == "store:categories":
        await q.answer()
        db = context.application.bot_data["db"]
        rows = await (await db.execute(
            "SELECT DISTINCT category FROM files WHERE active=1 ORDER BY category"
        )).fetchall()
        cats = [r["category"] for r in rows if r["category"]]
        await q.message.reply_text(
            "📂 <b>STORE CATEGORIES</b>\n\nChoose a category:",
            parse_mode="HTML", reply_markup=category_keyboard(cats)
        )
    elif data.startswith("store:cat:"):
        await q.answer()
        cat = data.split(":", 2)[2]
        await render_store(q.message, context, 0, cat)
    elif data == "store:search":
        await q.answer()
        context.user_data["store_state"] = "search"
        await q.message.reply_text(
            "🔎 <b>SEARCH STORE</b>\n\nSend a file name, category or tag:",
            parse_mode="HTML"
        )

async def store_search_router(update, context):
    # Admin multi-step actions have priority over store search.
    if context.user_data.get("admin_state"):
        return False
    if context.user_data.get("store_state") != "search":
        return False
    text = (update.effective_message.text or "").strip()
    if not text:
        return True
    context.user_data.pop("store_state", None)
    db = context.application.bot_data["db"]
    like = f"%{text}%"
    rows = await (await db.execute(
        "SELECT * FROM files WHERE active=1 AND (name LIKE ? OR description LIKE ? OR category LIKE ? OR tags LIKE ?) ORDER BY id DESC LIMIT 20",
        (like, like, like, like)
    )).fetchall()
    if not rows:
        await update.effective_message.reply_text("🔎 No matching files found.")
        return True
    await update.effective_message.reply_text(
        "🔎 <b>SEARCH RESULTS</b>\n\nSelect a file:",
        parse_mode="HTML",
        reply_markup=file_list_keyboard(rows, 0, False, False)
    )
    return True


async def cancel_purchase(update, context):
    q = update.callback_query
    await q.answer("Purchase cancelled.")
    try:
        await q.message.delete()
    except Exception:
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
