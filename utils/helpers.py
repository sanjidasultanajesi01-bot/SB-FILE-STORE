from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

# Consistent premium bot voice: short sections, visual separators and emojis.
def card(title, body="", icon="💎"):
    return f"{icon} <b>{title}</b>\n\n{body}\n\n━━━━━━━━━━━━━━"

def success(title, body=""):
    return card(title, body, "✅")

def error(title, body=""):
    return card(title, body, "❌")

def info(title, body=""):
    return card(title, body, "✨")


def html_escape(value):
    from html import escape
    return escape(str(value or ''), quote=False)
