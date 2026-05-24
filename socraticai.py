import os
from pathlib import Path
from google import genai
from google.genai import types


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


# 1. Load environment variables from the .env file
load_env_file(Path(__file__).resolve().with_name(".env"))


def get_api_key() -> str | None:
    for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
        key_value = os.getenv(key_name)
        if key_value:
            return key_value
    return None


# Verify that the API key was successfully parsed
api_key = get_api_key()
if not api_key:
    print("❌ Error: No API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env.")
    exit()

# 2. Initialize the modern GenAI Client
# Use the resolved API key explicitly so the SDK does not depend on env lookup.
try:
    client = genai.Client(api_key=api_key)
except Exception as exc:
    message = str(exc)
    if "API key not valid" in message or "API_KEY_INVALID" in message:
        print("❌ Error: The API key in .env is invalid. Replace it with a valid Gemini API key from Google AI Studio.")
        exit()
    raise

# 3. Configure the Socratic persona context
system_instruction = """
You are a Socratic Tutor. Your goal is to help the user understand physics concepts and engineering topics.
Do NOT give direct answers or write out full solutions immediately.
Instead, ask guiding questions, highlight logical gaps, and encourage the user to think through the core principles step-by-step.
Keep your responses conversational, supportive, and concise.
"""

# Configure the session parameters
config = types.GenerateContentConfig(
    system_instruction=system_instruction,
    temperature=0.7
)

# 4. Spin up a stateful, managed multi-turn conversation session
# Using 'gemini-2.5-flash' for optimized speed and intelligence
chat = client.chats.create(model="gemini-2.5-flash", config=config)

print("🎓 Modern Socratic CLI Tutor Initialized! (Type 'exit' to quit)")
print("🤖 AI: What physics or data structure topic would you like to explore today?")

# 5. Continuous Execution Loop
while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            print("Goodbye! Keep learning.")
            break
            
        if not user_input.strip():
            continue

        # Send the user prompt through the managed chat pipeline
        response = chat.send_message(user_input)
        print(f"\n🤖 AI: {response.text}")
        
    except Exception as e:
        print(f"\n❌ Execution Error: {e}")
        break