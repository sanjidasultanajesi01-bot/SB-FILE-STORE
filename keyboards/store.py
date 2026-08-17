
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def ib(text: str, data: str, style: str = "primary"):
    return InlineKeyboardButton(text=text, callback_data=data, style=style)

def file_list_keyboard(files, page: int, has_prev: bool, has_next: bool):
    rows = []
    for f in files:
        name = str(f["name"])[:48]
        rows.append([ib(f"📄 {name}  •  ৳{f['price']}", f"details:{f['id']}", "primary")])
    nav = []
    if has_prev:
        nav.append(ib("⬅️ Previous", f"store:page:{page-1}", "primary"))
    if has_next:
        nav.append(ib("Next ➡️", f"store:page:{page+1}", "success"))
    if nav:
        rows.append(nav)
    rows.append([
        ib("🔎 Search", "store:search", "primary"),
        ib("📂 Categories", "store:categories", "success"),
    ])
    return InlineKeyboardMarkup(rows)

def category_keyboard(categories):
    rows = []
    for c in categories:
        rows.append([ib(f"📂 {str(c)[:50]}", f"store:cat:{c}", "primary")])
    rows.append([ib("◀️ All Files", "store:page:0", "success")])
    return InlineKeyboardMarkup(rows)

def file_detail_keyboard(fid: int):
    return InlineKeyboardMarkup([
        [ib("💳 BUY NOW", f"buy:{fid}", "success"),
         ib("📦 MY PURCHASES", "user:purchases", "primary")],
        [ib("◀️ Back to Store", "store:page:0", "primary")],
    ])

def purchase_confirm_keyboard(fid: int):
    return InlineKeyboardMarkup([
        [ib("✅ CONFIRM PURCHASE", f"confirm:{fid}", "success")],
        [ib("❌ CANCEL", f"cancel:{fid}", "danger")],
    ])
