import aiosqlite
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance INTEGER NOT NULL DEFAULT 0,
 joined_at TEXT NOT NULL, last_reward TEXT, banned INTEGER NOT NULL DEFAULT 0,
 reward_count INTEGER NOT NULL DEFAULT 0, referrals INTEGER NOT NULL DEFAULT 0,
 referral_earned INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS files(
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '',
 category TEXT DEFAULT 'General', price INTEGER NOT NULL CHECK(price>=0),
 file_id TEXT NOT NULL, file_type TEXT NOT NULL, thumbnail_id TEXT, version TEXT,
 tags TEXT, active INTEGER NOT NULL DEFAULT 1, purchases INTEGER NOT NULL DEFAULT 0,
 downloads INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS purchases(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, file_id INTEGER NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(user_id,file_id), FOREIGN KEY(user_id) REFERENCES users(id),
 FOREIGN KEY(file_id) REFERENCES files(id));
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,amount INTEGER NOT NULL,
 kind TEXT NOT NULL,description TEXT,created_at TEXT NOT NULL,balance_after INTEGER NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS redeem_codes(
 code TEXT PRIMARY KEY, amount INTEGER NOT NULL, usage_limit INTEGER NOT NULL DEFAULT 1,
 used_count INTEGER NOT NULL DEFAULT 0, expires_at TEXT, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS redeemed_codes(code TEXT,user_id INTEGER,redeemed_at TEXT,PRIMARY KEY(code,user_id));
CREATE TABLE IF NOT EXISTS referrals(referrer_id INTEGER,referee_id INTEGER UNIQUE,created_at TEXT);
CREATE TABLE IF NOT EXISTS channels(id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id TEXT UNIQUE,title TEXT,
 invite_link TEXT,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS payments(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,package_name TEXT,
 coins INTEGER,amount REAL,proof_file_id TEXT,status TEXT DEFAULT 'pending',created_at TEXT);
CREATE TABLE IF NOT EXISTS payment_packages(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,coins INTEGER,price REAL,active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS support_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,message TEXT,
 status TEXT DEFAULT 'open',created_at TEXT);
CREATE TABLE IF NOT EXISTS staff(user_id INTEGER PRIMARY KEY,role TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE IF NOT EXISTS stored_links(token TEXT PRIMARY KEY,owner_id INTEGER,chat_id INTEGER,message_id INTEGER,
 created_at TEXT,expires_at TEXT,usage_limit INTEGER,usage_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,owner_id INTEGER,description TEXT,created_at TEXT,
 access_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS batch_items(batch_id TEXT,message_id INTEGER,PRIMARY KEY(batch_id,message_id));
CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT,details TEXT,created_at TEXT);
CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id,created_at);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at);
"""

class DB:
    def __init__(self,path): self.path=path
    async def connect(self):
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        db=await aiosqlite.connect(self.path); db.row_factory=aiosqlite.Row
        await db.executescript(SCHEMA); await db.commit(); return db

async def fetchone(conn, sql, params=()):
    cur = await conn.execute(sql, params)
    try:
        return await cur.fetchone()
    finally:
        await cur.close()
