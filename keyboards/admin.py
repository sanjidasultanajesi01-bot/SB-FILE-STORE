from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def ib(text: str, data: str, style: str = "primary") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data, style=style)


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [ib("📊 Statistics", "admin:stats", "primary"), ib("📁 File Management", "admin:files", "success")],
        [ib("📢 Force Join", "admin:force", "primary"), ib("💎 Coin Management", "admin:coins", "success")],
        [ib("🎟️ Redeem Codes", "admin:redeem", "primary"), ib("👥 User Management", "admin:users", "primary")],
        [ib("📣 Broadcast", "admin:broadcast", "success"), ib("💳 Payments", "admin:payments", "success")],
        [ib("🆘 Support", "admin:support", "primary"), ib("⚙️ Settings", "admin:settings", "primary")],
        [ib("🔗 Stored Links", "admin:links", "primary"), ib("📋 Logs", "admin:logs", "danger")],
        [ib("🔄 Refresh", "admin:home", "primary")],
    ])


def force_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [ib("➕ Add Channel", "admin:force:add", "success")],
        [ib("📋 Channel List", "admin:force:list", "primary")],
        [ib("🗑️ Remove Channel", "admin:force:remove", "danger")],
        [ib("◀️ Back", "admin:home", "primary")],
    ])


def file_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [ib("➕ Add File", "admin:file:add", "success")],
        [ib("📋 All Files", "admin:file:list", "primary")],
        [ib("🔍 Search File", "admin:file:search", "primary")],
        [ib("🗑️ Delete File", "admin:file:delete", "danger")],
        [ib("◀️ Back", "admin:home", "primary")],
    ])


def payment_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [ib("📱 bKash Settings", "admin:payments:settings", "success")],
        [ib("💎 Coin Packages", "admin:payments:packages", "primary")],
        [ib("◀️ Back", "admin:home", "primary")],
    ])
