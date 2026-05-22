import time

import anthropic

from config import ANTHROPIC_API_KEY, LLM_MODEL, MAX_HISTORY
from database import append, tail
from prompt import build_system_prompt
from tools import TOOL_REGISTRY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FRAMEWORK_INJECTED_CHAT_ID = {
    "create_reminder",
    "list_reminders",
    "cancel_reminder",
}

MAX_TOOL_ITERATIONS = 5


def _run_tool(tool_use, chat_id: str) -> str:
    name = tool_use.name
    if name not in TOOL_REGISTRY:
        return f"כלי לא מוכר: {name}"
    tool_input = dict(tool_use.input or {})
    if name in FRAMEWORK_INJECTED_CHAT_ID:
        tool_input["chat_id"] = chat_id
    try:
        return str(TOOL_REGISTRY[name]["fn"](**tool_input))
    except Exception as e:
        return f"שגיאה בהפעלת הכלי {name}: {e}"


def handle_message(chat_id: str, sender_name: str, message_text: str) -> str:
    append(chat_id, "user", message_text)

    history = tail(chat_id, MAX_HISTORY)
    system_prompt = build_system_prompt(TOOL_REGISTRY)
    tools = [td["schema"] for td in TOOL_REGISTRY.values()]

    messages = history[:-1]  # exclude the message we just appended, we add it as last
    messages.append({"role": "user", "content": message_text})

    kwargs = {
        "model": LLM_MODEL,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    reply_text = ""
    for _ in range(MAX_TOOL_ITERATIONS):
        response = None
        for attempt in range(3):
            try:
                response = _client.messages.create(**kwargs)
                break
            except anthropic.APIStatusError as e:
                if e.status_code != 529:
                    raise
                if attempt < 2:
                    time.sleep(3)
                else:
                    return "מצטער, השירות עמוס כרגע. נסה שוב בעוד דקה."
        if response is None:
            return "מצטער, השירות לא זמין כרגע."

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    reply_text = block.text
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _run_tool(block, chat_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            kwargs["messages"] = kwargs["messages"] + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results},
            ]
        else:
            reply_text = "מצטער, לא הצלחתי לעבד את הבקשה."
            break
    else:
        reply_text = "מצטער, הבקשה דרשה יותר מדי שלבים. אנא נסח מחדש."

    if not reply_text:
        reply_text = "קיבלתי, מטפל בזה."

    append(chat_id, "assistant", reply_text)
    return reply_text
