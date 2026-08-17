from telegram import Update
from telegram.ext import ContextTypes
from services.payment_service import seed_packages, get_payment_settings
from utils.helpers import html_escape

async def payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    settings = await get_payment_settings(db)
    number = settings["bkash_number"] or "Not configured"
    instructions = settings["payment_instructions"]
    await update.message.reply_text(
        "💳 <b>ADD COINS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 <b>bKash Number:</b> <code>{html_escape(number)}</code>\n\n"
        f"📝 {html_escape(instructions)}\n\n"
        "⚠️ After payment, submit your transaction ID/proof for admin approval.",
        parse_mode="HTML"
    )

async def payments(update, context):
    db=context.application.bot_data["db"]
    await seed_packages(db)
    rows=await (await db.execute(
        "SELECT * FROM payment_packages WHERE active=1"
    )).fetchall()
    text = "\n".join(f"💎 {r['coins']} Coins — ৳{r['price']}" for r in rows)
    await update.message.reply_text(
        "💳 <b>COIN PACKAGES</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"+text+
        "\n\n👇 Use /payment to view payment instructions.",
        parse_mode="HTML"
    )
