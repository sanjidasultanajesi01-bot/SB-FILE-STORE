import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _ids(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}

@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]
    bot_username: str
    support_username: str
    currency_name: str
    daily_reward: int
    referral_reward: int
    db_path: str
    payment_provider: str
    payment_api_key: str

def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "8989266640:AAENqpwF5lpgeS8i97VU8jprmYOpE7jsJTw").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    return Config(
        token, _ids(os.getenv("ADMIN_IDS","6896959301")), os.getenv("BOT_USERNAME","SABBIR CODEX").strip().lstrip("@"),
        os.getenv("SUPPORT_USERNAME","mksedt").strip().lstrip("@"), os.getenv("CURRENCY_NAME","Coins"),
        int(os.getenv("DAILY_REWARD","20")), int(os.getenv("REFERRAL_REWARD","20")),
        os.getenv("DB_PATH","data/store.db"), os.getenv("PAYMENT_PROVIDER","").strip(),
        os.getenv("PAYMENT_API_KEY","").strip())
