
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.user import main_menu
from utils.helpers import html_escape

def _menu(update, context):
    return main_menu(is_admin=update.effective_user.id in context.application.bot_data["cfg"].admin_ids)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    r = await (await db.execute("SELECT * FROM users WHERE id=?", (update.effective_user.id,))).fetchone()
    if not r:
        await update.message.reply_text("❌ Profile not found. Please use /start first.")
        return
    purchases = await count(db, "purchases", r["id"])
    await update.message.reply_text(
        "📊 <b>MY PROFILE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Name:</b> {html_escape(r['first_name'] or 'User')}\n"
        f"🔗 <b>Username:</b> @{html_escape(r['username']) if r['username'] else '—'}\n"
        f"🆔 <b>Telegram ID:</b> <code>{r['id']}</code>\n"
        f"💰 <b>Balance:</b> ৳{r['balance']}\n"
        f"📦 <b>Total Purchases:</b> {purchases}\n"
        f"🤝 <b>Referrals:</b> {r['referrals']}\n"
        f"🎁 <b>Rewards Claimed:</b> {r['reward_count']}\n"
        f"📅 <b>Joined:</b> {html_escape(r['joined_at'])}",
        parse_mode="HTML", reply_markup=_menu(update, context)
    )

async def count(db, table, uid):
    allowed = {"purchases"}
    if table not in allowed:
        raise ValueError("Invalid count table")
    row = await (await db.execute(f"SELECT COUNT(*) n FROM {table} WHERE user_id=?", (uid,))).fetchone()
    return int(row["n"] if row else 0)

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    r = await (await db.execute("SELECT balance FROM users WHERE id=?", (update.effective_user.id,))).fetchone()
    balance = int(r["balance"] if r else 0)
    await update.message.reply_text(
        "💎 <b>MY WALLET</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {html_escape(update.effective_user.first_name or 'User')}\n"
        f"🆔 <code>{update.effective_user.id}</code>\n"
        f"💰 <b>Balance: ৳{balance}</b>\n\n"
        "💳 Use <b>Buy Credits</b> to add balance.\n"
        "📜 Your wallet changes are recorded in the transaction history.",
        parse_mode="HTML", reply_markup=_menu(update, context)
    )
