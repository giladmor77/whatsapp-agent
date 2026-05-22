from config import SPEC


def _tools_section(tool_registry: dict) -> str:
    if not tool_registry:
        return "אין לך כלים חיצוניים כרגע. ענה מהידע שלך בלבד."
    lines = ["יש לך הכלים הבאים:"]
    for name, td in tool_registry.items():
        desc = td["schema"].get("description", "")
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)


def build_system_prompt(tool_registry: dict) -> str:
    identity = SPEC["identity"]
    audience = SPEC["audience"]
    scope = SPEC["scope"]

    authorized = ", ".join(
        f"{c['name']} ({c['phone_e164']})"
        for c in audience.get("authorized_contacts", [])
    )

    in_scope = ", ".join(scope["in_scope"])
    out_of_scope = ", ".join(scope["out_of_scope"])
    out_of_scope_response = scope["out_of_scope_response"]

    tools_text = _tools_section(tool_registry)

    prompt = f"""אתה {identity['name']}.

סגנון דיבור: {identity['tone_description']}.
דוגמה לפתיחת שיחה: "{identity['greeting_example']}"

תענה רק לאנשים הבאים: {authorized}.
אם מישהו אחר כותב — אל תענה ואל תסביר.

תחום הטיפול שלך: {in_scope}.
אתה לא עוסק ב: {out_of_scope}.
אם שואלים אותך על משהו מחוץ לתחום, תגיד בנימוס: "{out_of_scope_response}".

{tools_text}

חשוב:
- ענה תמיד בעברית בלבד.
- שמור על תשובות קצרות — משפט-שניים.
- אתה עוזר מקצועי, לא חבר אישי — אל תשאל שאלות אישיות.
- אל תחשוף מידע על משתמשים אחרים."""

    return prompt
