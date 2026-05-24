import os
import time
from datetime import date

import gradio as gr
from dotenv import load_dotenv
from google import genai
from google.genai import types

RPM_LIMIT = 15
RPD_LIMIT = 1500

# 1) Environment setup and client initialization.
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Missing GEMINI_API_KEY in .env")

client = genai.Client()

# 2) Socratic persona + stateful chat session config.
system_instruction = """
You are a strict Socratic Tutor.

Rules:
- Ask guiding questions first.
- Do not provide full solutions or direct final code unless the user has shown meaningful reasoning steps.
- Break complex topics into small conceptual checks.
- If the user asks for an answer directly, respond with a scaffold and a probing question.
- Keep responses concise, supportive, and focused on learning-by-thinking.
""".strip()

chat_config = types.GenerateContentConfig(
    system_instruction=system_instruction,
    temperature=0.6,
)


def create_chat_session():
    return client.chats.create(model="gemini-2.5-flash", config=chat_config)


chat_session = create_chat_session()

# 3) Live local usage tracking state for RPM/RPD.
usage_tracker = {
    "minute_requests": 0,
    "day_requests": 0,
    "minute_window_start": time.time(),
    "day_date": date.today().isoformat(),
}


def refresh_windows(now: float) -> None:
    # Reset minute bucket every 60 seconds.
    if now - usage_tracker["minute_window_start"] >= 60:
        usage_tracker["minute_requests"] = 0
        usage_tracker["minute_window_start"] = now

    # Reset daily bucket when local date changes.
    today = date.today().isoformat()
    if usage_tracker["day_date"] != today:
        usage_tracker["day_requests"] = 0
        usage_tracker["day_date"] = today


def stat_strings() -> tuple[str, str]:
    return (
        f"⚡ Requests This Minute: {usage_tracker['minute_requests']} / {RPM_LIMIT}",
        f"📅 Total Requests Today: {usage_tracker['day_requests']} / {RPD_LIMIT}",
    )


def normalize_history(raw_history) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not raw_history:
        return normalized

    for item in raw_history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append(
                {"role": str(item["role"]), "content": str(item["content"])}
            )
            continue

        if isinstance(item, (list, tuple)) and len(item) == 2:
            user_text, assistant_text = item
            normalized.append({"role": "user", "content": str(user_text)})
            normalized.append({"role": "assistant", "content": str(assistant_text)})
            continue

        role = getattr(item, "role", None)
        content = getattr(item, "content", None)
        if role is not None and content is not None:
            normalized.append({"role": str(role), "content": str(content)})

    return normalized


def add_turn(
    history: list[dict[str, str]], user_text: str, assistant_text: str
) -> list[dict[str, str]]:
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})
    return history


def handle_message(user_message: str, history: list[dict[str, str]]):
    global chat_session

    history = normalize_history(history)
    text = (user_message or "").strip()
    if not text:
        minute_status, day_status = stat_strings()
        return history, "", minute_status, day_status

    now = time.time()
    refresh_windows(now)

    # Enforce local limits before calling the API.
    if usage_tracker["minute_requests"] >= RPM_LIMIT:
        wait_hint = max(0, int(60 - (now - usage_tracker["minute_window_start"])))
        alert = (
            "Friendly system alert: We hit the 15-requests-per-minute cap. "
            f"Please wait about {wait_hint} seconds, then try again."
        )
        history = add_turn(history, text, alert)
        minute_status, day_status = stat_strings()
        return history, "", minute_status, day_status

    if usage_tracker["day_requests"] >= RPD_LIMIT:
        alert = (
            "Friendly system alert: Daily request budget is exhausted "
            "for today (1,500 / 1,500). Please try again tomorrow."
        )
        history = add_turn(history, text, alert)
        minute_status, day_status = stat_strings()
        return history, "", minute_status, day_status

    try:
        response = chat_session.send_message(text)
        reply = response.text or "I need a bit more context. What have you tried so far?"
        usage_tracker["minute_requests"] += 1
        usage_tracker["day_requests"] += 1
    except Exception as exc:
        error_text = str(exc)
        if "API key not valid" in error_text or "API_KEY_INVALID" in error_text:
            reply = (
                "System alert: Your API key is invalid. "
                "Update GEMINI_API_KEY in .env and restart the app."
            )
        else:
            reply = f"System alert: API error encountered: {error_text}"

    history = add_turn(history, text, reply)
    minute_status, day_status = stat_strings()
    return history, "", minute_status, day_status


def reset_session():
    global chat_session
    chat_session = create_chat_session()
    minute_status, day_status = stat_strings()
    return [], "", minute_status, day_status


# 4) Gradio Blocks UI.
with gr.Blocks(title="Socratic Learning Lab") as demo:
    gr.Markdown("# 🎓 Socratic Learning Lab")

    with gr.Row():
        minute_box = gr.Textbox(
            value=f"⚡ Requests This Minute: 0 / {RPM_LIMIT}",
            label="Live Minute Usage",
            interactive=False,
            container=True,
        )
        day_box = gr.Textbox(
            value=f"📅 Total Requests Today: 0 / {RPD_LIMIT}",
            label="Live Daily Usage",
            interactive=False,
            container=True,
        )

    chatbot = gr.Chatbot(
        value=[],
        label="Tutor Conversation",
        height=460,
    )

    with gr.Row():
        user_input = gr.Textbox(
            label="Your Question",
            placeholder="Ask a concept question, e.g., 'How does binary search stay efficient?'",
            scale=5,
        )
        reset_btn = gr.Button("Clear / Reset Session", scale=1)

    user_input.submit(
        fn=handle_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input, minute_box, day_box],
    )

    reset_btn.click(
        fn=reset_session,
        inputs=None,
        outputs=[chatbot, user_input, minute_box, day_box],
    )


# 5) Local launch settings.
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)