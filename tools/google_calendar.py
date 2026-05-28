from datetime import datetime, timezone, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import config
from tools import TOOL_REGISTRY


def _service():
    creds = Credentials(
        token=None,
        refresh_token=config.GOOGLE_REFRESH_TOKEN,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("calendar", "v3", credentials=creds)


def list_events(time_min_iso: str = None, time_max_iso: str = None) -> str:
    svc = _service()
    now = datetime.now(timezone.utc)
    t_min = time_min_iso or now.isoformat()
    t_max = time_max_iso or (now + timedelta(days=7)).isoformat()

    result = svc.events().list(
        calendarId="primary",
        timeMin=t_min,
        timeMax=t_max,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = result.get("items", [])
    if not events:
        return "אין אירועים בתקופה זו."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        try:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            start_str = dt.strftime("%d/%m %H:%M")
        except Exception:
            start_str = start
        lines.append(f"• {start_str} — {e.get('summary', 'ללא שם')}")
    return "\n".join(lines)


def create_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> str:
    svc = _service()
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Jerusalem"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Jerusalem"},
    }
    created = svc.events().insert(calendarId="primary", body=event).execute()
    return f"פגישה '{summary}' נוצרה בהצלחה (ID: {created.get('id')})"


def delete_event(event_id: str) -> str:
    svc = _service()
    svc.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"האירוע {event_id} נמחק."


TOOL_REGISTRY["list_calendar_events"] = {
    "schema": {
        "name": "list_calendar_events",
        "description": "מציג אירועים ביומן גוגל בין שני תאריכים. השתמש כשהמשתמש שואל מה יש לו ביומן, אילו פגישות יש, מה התוכנית.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min_iso": {"type": "string", "description": "תחילת טווח החיפוש, פורמט ISO 8601. השמט לקבלת אירועים מהיום."},
                "time_max_iso": {"type": "string", "description": "סוף טווח החיפוש, פורמט ISO 8601. השמט לקבלת 7 ימים קדימה."},
            },
            "required": [],
        },
    },
    "fn": list_events,
}

TOOL_REGISTRY["create_calendar_event"] = {
    "schema": {
        "name": "create_calendar_event",
        "description": "יוצר אירוע חדש ביומן גוגל. השתמש כשהמשתמש מבקש לקבוע פגישה, לזמן ישיבה, להוסיף אירוע.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "שם/כותרת האירוע"},
                "start_iso": {"type": "string", "description": "זמן התחלה, פורמט ISO 8601 עם offset ישראלי (למשל 2026-05-28T10:00:00+03:00)"},
                "end_iso": {"type": "string", "description": "זמן סיום, פורמט ISO 8601"},
                "description": {"type": "string", "description": "תיאור אופציונלי לאירוע"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    "fn": create_event,
}

TOOL_REGISTRY["delete_calendar_event"] = {
    "schema": {
        "name": "delete_calendar_event",
        "description": "מוחק אירוע מהיומן לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "מזהה האירוע למחיקה"},
            },
            "required": ["event_id"],
        },
    },
    "fn": delete_event,
}
