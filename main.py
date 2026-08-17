import logging
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,ConversationHandler,filters
from config import load_config
from database.db import DB
from utils.logger import setup_logging
from handlers.start import start
from handlers.force_join import fj_check
from handlers.user import profile,wallet
from handlers.store import store,buy,details,confirm_purchase,cancel_purchase,store_callback,store_search_router
from handlers.reward import reward
from handlers.leaderboard import leaderboard
from handlers.referral import referral
from handlers.redeem import redeem_start,redeem_code
from handlers.purchases import purchases,redownload
from handlers.support import support
from handlers.payments import payment_info
from handlers.admin import admin,admin_button,admin_callback,admin_text_router,stats,setbkash,setpaymentinfo,payment_settings,addcoins,removecoins,channels_cmd,removechannel_cmd,addchannel_cmd,addfile_cmd,delete_file_cmd,ban_user,unban_user
from handlers.broadcast import broadcast
from handlers.payments import payments

async def error_handler(update,context):
    logging.getLogger("bot").error("Unhandled Telegram error: %s", type(context.error).__name__)
    if update and getattr(update,"effective_message",None):
        try: await update.effective_message.reply_text("❌ Something went wrong. Please try again later.")
        except Exception: pass

async def post_init(app):
    db=await DB(app.bot_data["cfg"].db_path).connect()
    app.bot_data["db"]=db
    me = await app.bot.get_me()
    app.bot_data["bot_username"] = me.username or "Premium File Store"
    from services.payment_service import seed_packages
    await seed_packages(db)

def main():
    setup_logging(); cfg=load_config()
    app=Application.builder().token(cfg.bot_token).post_init(post_init).build()
    app.bot_data["cfg"]=cfg
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler(["profile"],profile)); app.add_handler(CommandHandler("wallet",wallet))
    app.add_handler(CommandHandler("store",store)); app.add_handler(CommandHandler("reward",reward))
    app.add_handler(CommandHandler("referral",referral)); app.add_handler(CommandHandler("purchases",purchases))
    app.add_handler(CommandHandler("support",support)); app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CommandHandler("stats",stats)); app.add_handler(CommandHandler("broadcast",broadcast))
    app.add_handler(CommandHandler("leaderboard",leaderboard))
    app.add_handler(CommandHandler("deletefile",delete_file_cmd))
    app.add_handler(CommandHandler("ban",ban_user))
    app.add_handler(CommandHandler("unban",unban_user))
    app.add_handler(CommandHandler("addcoins", addcoins))
    app.add_handler(CommandHandler("removecoins", removecoins))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("removechannel", removechannel_cmd))
    app.add_handler(CommandHandler("addchannel", addchannel_cmd))
    app.add_handler(CommandHandler("addfile", addfile_cmd))
    app.add_handler(CommandHandler("payments",payments))
    app.add_handler(CommandHandler("payment",payment_info))
    app.add_handler(CommandHandler("setbkash",setbkash))
    app.add_handler(CommandHandler("setpaymentinfo",setpaymentinfo))
    app.add_handler(CommandHandler("paymentsettings",payment_settings))
    app.add_handler(CallbackQueryHandler(fj_check,pattern=r"^fj:check$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin:"))
    app.add_handler(CallbackQueryHandler(details,pattern=r"^details:\d+$"))
    app.add_handler(CallbackQueryHandler(buy,pattern=r"^buy:\d+$"))
    app.add_handler(CallbackQueryHandler(confirm_purchase,pattern=r"^confirm:\d+$"))
    app.add_handler(CallbackQueryHandler(store_callback,pattern=r"^store:"))
    app.add_handler(CallbackQueryHandler(cancel_purchase,pattern=r"^cancel:\d+$"))
    app.add_handler(CallbackQueryHandler(redownload,pattern=r"^purchase:get:\d+$"))
    app.add_handler(ConversationHandler(entry_points=[MessageHandler(filters.Regex(r"^🎟️ Redeem Code 〽️$"),redeem_start)],
        states={1:[MessageHandler(filters.TEXT & ~filters.COMMAND,redeem_code)]},fallbacks=[]))
    app.add_handler(MessageHandler(filters.Regex(r"^👑 Admin Commands 〽️$"),admin_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, store_search_router), group=-2)
    app.add_handler(MessageHandler(filters.ALL, admin_text_router), group=-1)
    app.add_handler(MessageHandler(filters.Regex(r"^🛍️ File Store 〽️$"),store))
    app.add_handler(MessageHandler(filters.Regex(r"^💎 My Wallet 〽️$"),wallet))
    app.add_handler(MessageHandler(filters.Regex(r"^🎁 Daily Reward 〽️$"),reward))
    app.add_handler(MessageHandler(filters.Regex(r"^🤝 Refer & Earn 〽️$"),referral))
    app.add_handler(MessageHandler(filters.Regex(r"^👤 My Profile 〽️$"),profile))
    app.add_handler(MessageHandler(filters.Regex(r"^📦 My Purchases 〽️$"),purchases))
    app.add_handler(MessageHandler(filters.Regex(r"^🏆 Leaderboard 〽️$"),leaderboard))
    app.add_handler(MessageHandler(filters.Regex(r"^🆘 Help & Support 〽️$"),support))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=["message","callback_query"])
if __name__=="__main__": main()
