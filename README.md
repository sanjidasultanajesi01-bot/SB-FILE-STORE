# Premium File Store Bot

Production-oriented Telegram digital file store built with Python 3.10+, python-telegram-bot 21.x, SQLite/aiosqlite and dotenv.

## Install
Python 3.10+ is required.
`pip install -r requirements.txt`

Copy `.env.example` to `.env` and set `BOT_TOKEN` and `ADMIN_IDS`.

## Run
`python main.py`

## Checks
`python check.py`
`python -m compileall .`

## BotFather
Create a bot with BotFather and place its token in `.env`. `BOT_USERNAME` should be the bot username without `@`.

## Force Join
Add required channel rows to the `channels` table with the bot as a member/admin and a valid invite/public link. Membership failures are fail-closed.

## Deployment
VPS/Linux/Windows: install Python, install requirements, configure `.env`, run `python main.py`.
Termux: install Python and pip, clone/copy the project, `pip install -r requirements.txt`, configure `.env`, then `python main.py`.
Render/Railway: use Python 3.10+ and start command `python main.py`; persistent storage is required for SQLite.

## Security
Secrets belong in `.env`, never in source. Do not commit `.env`. Admin access is controlled by `ADMIN_IDS`.

## Current architecture
The project contains the database, wallet/purchase/referral/reward/redeem/force-join/link/payment/broadcast service layers and modular handlers. Advanced stored-link and batch tables are ready for extension without exposing database IDs.

## Colorful Telegram buttons
The project uses Telegram's native button styles: `primary` (blue), `success` (green), and `danger` (red). These styles require a recent Telegram client and python-telegram-bot 22.7+; older clients may show the normal button appearance. Telegram documents the styles as blue/green/red.


## Store UI update
- Files are displayed as a clean vertical list like a premium Telegram store.
- Clicking a file opens its full description, category, tags, version and Bangladeshi Taka price.
- Purchase requires an explicit confirmation.
- Store pagination, categories and search are included.
- Force Join Add Channel now requires only the channel ID. The bot fetches the title automatically and uses a public link or creates an invite link when Telegram permissions allow it.
- Main-menu buttons use Telegram's supported button styles (blue/green/red); the final appearance is controlled by the Telegram client.


## Update applied to this existing project
- Preserved the existing UI/layout and existing button color styles.
- Added working Leaderboard button and `/leaderboard`.
- Fixed Broadcast from Admin Commands and `/broadcast` (reply-to-message or next-message mode).
- Added working File Delete in File Management and `/deletefile`.
- Existing purchased files are archived instead of deleting purchase history.
- Added functional User Management listing and `/ban` `/unban`.
- Added functional Redeem Code creation from Admin Commands.
- Added Logs, Settings, Support Tickets and Stored Links views.
- Admin multi-step input now has priority over store search.
- Added banned-user access protection.
