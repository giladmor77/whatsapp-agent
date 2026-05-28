from datetime import datetime
from pathlib import Path

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import DATABASE_PATH
from tools import TOOL_REGISTRY

# Ensure the data directory exists before APScheduler tries to create the jobstore
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

_jobstore_url = f"sqlite:///{DATABASE_PATH}"
_scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=_jobstore_url)}
)
_scheduler.start()


def _fire_reminder(chat_id: str, message: str) -> None:
    from tools.whatsapp import send_reply
    send_reply(chat_id, f"⏰ תזכורת: {message}")


def create_reminder(chat_id: str, remind_at_iso: str, message: str) -> str:
    """chat_id will be filled by the framework; leave empty"""
    run_time = datetime.fromisoformat(remind_at_iso)
    job = _scheduler.add_job(
        _fire_reminder,
        "date",
        run_date=run_time,
        kwargs={"chat_id": chat_id, "message": message},
    )
    return f"תזכורת נקבעה ל-{run_time.strftime('%d/%m/%Y %H:%M')} — '{message}' (מזהה: {job.id})"


def list_reminders(chat_id: str) -> str:
    """chat_id will be filled by the framework; leave empty"""
    jobs = [j for j in _scheduler.get_jobs() if j.kwargs.get("chat_id") == chat_id]
    if not jobs:
        return "אין תזכורות פעילות."
    lines = []
    for j in jobs:
        t = j.next_run_time.strftime("%d/%m/%Y %H:%M") if j.next_run_time else "?"
        lines.append(f"• {t} — {j.kwargs.get('message', '')} (מזהה: {j.id})")
    return "\n".join(lines)


def cancel_reminder(chat_id: str, reminder_id: str) -> str:
    """chat_id will be filled by the framework; leave empty"""
    job = _scheduler.get_job(reminder_id)
    if not job or job.kwargs.get("chat_id") != chat_id:
        return "לא נמצאה תזכורת עם המזהה הזה."
    _scheduler.remove_job(reminder_id)
    return "התזכורת בוטלה."


TOOL_REGISTRY["create_reminder"] = {
    "schema": {
        "name": "create_reminder",
        "description": "קובע תזכורת שתישלח ב-WhatsApp בזמן מסוים",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "chat_id will be filled by the framework; leave empty"},
                "remind_at_iso": {"type": "string", "description": "מתי לשלוח את התזכורת, בפורמט ISO 8601 (לדוגמה: 2026-05-22T15:00:00)"},
                "message": {"type": "string", "description": "תוכן התזכורת"},
            },
            "required": ["remind_at_iso", "message"],
        },
    },
    "fn": create_reminder,
}

TOOL_REGISTRY["list_reminders"] = {
    "schema": {
        "name": "list_reminders",
        "description": "מחזיר רשימת התזכורות הפעילות של המשתמש",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "chat_id will be filled by the framework; leave empty"},
            },
            "required": [],
        },
    },
    "fn": list_reminders,
}

TOOL_REGISTRY["cancel_reminder"] = {
    "schema": {
        "name": "cancel_reminder",
        "description": "מבטל תזכורת קיימת לפי מזהה",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "chat_id will be filled by the framework; leave empty"},
                "reminder_id": {"type": "string", "description": "מזהה התזכורת לביטול"},
            },
            "required": ["reminder_id"],
        },
    },
    "fn": cancel_reminder,
}
