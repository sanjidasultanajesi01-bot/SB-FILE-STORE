
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def join_keyboard(channels):
    rows = []
    for c in channels:
        link = c["invite_link"]
        if link:
            rows.append([InlineKeyboardButton(
                f"📢 {str(c['title'] or 'Required Channel')[:50]}",
                url=link, style="primary"
            )])
    rows.append([InlineKeyboardButton(
        "✅ I JOINED — CHECK AGAIN", callback_data="fj:check", style="success"
    )])
    return InlineKeyboardMarkup(rows)
