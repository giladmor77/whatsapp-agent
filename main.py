import importlib
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import ANSWER_GROUPS, AUTHORIZED_PHONES, GREEN_API_INSTANCE, SPEC
from database import append, init_db, is_processed, mark_processed
from tools.whatsapp import send_reply

# Import reminders to register tools before agent is loaded
if "reminders" in SPEC.get("tools", []):
    import tools.reminders  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

BOT_WID = f"972515402037@c.us"  # the bot's own WhatsApp ID


@app.get("/health")
def health():
    return {"status": "ok", "version": 1, "bot": SPEC["identity"]["name"]}


@app.post("/webhook/green-api")
async def webhook(request: Request):
    body = await request.json()

    if body.get("typeWebhook") != "incomingMessageReceived":
        return JSONResponse({"ok": True})

    id_message = body.get("idMessage", "")
    if not id_message or is_processed(id_message):
        return JSONResponse({"ok": True})

    sender_data = body.get("senderData", {})
    chat_id: str = sender_data.get("chatId", "")
    sender: str = sender_data.get("sender", chat_id)
    sender_name: str = sender_data.get("senderName", "")

    # Ignore own messages
    if sender == BOT_WID or chat_id == BOT_WID:
        return JSONResponse({"ok": True})

    # Ignore group messages if not configured to handle them
    if chat_id.endswith("@g.us") and not ANSWER_GROUPS:
        return JSONResponse({"ok": True})

    # Whitelist enforcement — only respond to authorized contacts
    sender_phone = sender.replace("@c.us", "").replace("@s.whatsapp.net", "")
    if SPEC["audience"]["mode"] == "whitelist" and sender_phone not in AUTHORIZED_PHONES:
        return JSONResponse({"ok": True})

    message_data = body.get("messageData", {})
    if message_data.get("typeMessage") != "textMessage":
        return JSONResponse({"ok": True})

    message_text: str = message_data.get("textMessageData", {}).get("textMessage", "")
    if not message_text.strip():
        return JSONResponse({"ok": True})

    mark_processed(id_message)

    from agent import handle_message
    reply = handle_message(chat_id, sender_name, message_text)
    send_reply(chat_id, reply)

    return JSONResponse({"ok": True})
