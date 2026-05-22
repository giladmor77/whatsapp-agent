import httpx

from config import GREEN_API_INSTANCE, GREEN_API_TOKEN, GREEN_API_URL


def send_reply(chat_id: str, text: str) -> None:
    url = f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE}/sendMessage/{GREEN_API_TOKEN}"
    httpx.post(url, json={"chatId": chat_id, "message": text}, timeout=10)


def send_to_phone(phone_e164: str, text: str) -> None:
    chat_id = f"{phone_e164}@c.us"
    send_reply(chat_id, text)
