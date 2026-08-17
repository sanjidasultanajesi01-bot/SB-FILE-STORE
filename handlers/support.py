from telegram.ext import ContextTypes
from utils.helpers import now
async def support(update,context):
    cfg=context.application.bot_data["cfg"]
    await update.message.reply_text(f"🆘 <b>Help & Support</b>\\n\\nContact: @{cfg.support_username}" if cfg.support_username else "🆘 Support username is not configured.",parse_mode="HTML")
