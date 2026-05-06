import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "scholarships.db"

CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "ellen.iforme@gmail.com")
USER_AGENT = f"grad-scholarship-bot/0.1 (+contact: {CONTACT_EMAIL})"

WEBHOOK_DOMESTIC = os.environ.get("DISCORD_WEBHOOK_DOMESTIC", "")
WEBHOOK_OVERSEAS = os.environ.get("DISCORD_WEBHOOK_OVERSEAS", "")

REQUEST_INTERVAL_SEC = 10
REMINDER_DAYS = (7, 3)
