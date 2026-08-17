from telegram import Update
from telegram.ext import ContextTypes
from utils.helpers import html_escape

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    rows = await (await db.execute(
        """SELECT id, first_name, username, balance, referrals
           FROM users WHERE banned=0
           ORDER BY balance DESC, referrals DESC, id ASC LIMIT 10"""
    )).fetchall()

    if not rows:
        text = (
            "🏆 <b>LEADERBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📭 No users yet."
        )
    else:
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(rows, 1):
            name = html_escape(r["first_name"] or r["username"] or f"User {r['id']}")
            if len(name) > 24:
                name = name[:24] + "…"
            icon = medals[i-1] if i <= 3 else f"<b>{i}.</b>"
            lines.append(
                f"{icon} <b>{name}</b>\n"
                f"   💰 ৳{int(r['balance'])}  •  🤝 {int(r['referrals'])} referrals"
            )
        text = (
            "🏆 <b>LEADERBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n" +
            "\n\n".join(lines) +
            "\n\n✨ Top 10 users by balance"
        )

    await update.effective_message.reply_text(text, parse_mode="HTML")
