
from telegram import KeyboardButton, ReplyKeyboardMarkup

def b(text: str, style: str) -> KeyboardButton:
    return KeyboardButton(text=text, style=style)

def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [b("🛍️ File Store 〽️", "success"), b("👤 My Profile 〽️", "primary")],
        [b("💎 My Wallet 〽️", "success"), b("🤝 Refer & Earn 〽️", "danger")],
        [b("🎁 Daily Reward 〽️", "success"), b("🎟️ Redeem Code 〽️", "primary")],
        [b("📦 My Purchases 〽️", "primary"), b("🏆 Leaderboard 〽️", "primary")],
        [b("🆘 Help & Support 〽️", "danger")],
    ]
    if is_admin:
        rows.append([b("👑 Admin Commands 〽️", "danger")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)
