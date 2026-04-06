import os
import json
import sys
try:
    from google import genai
except ImportError:
    import google.genai as genai
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()

PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def load_api_keys() -> dict:
    if not os.path.exists(API_CONFIG_PATH):
        return {}
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to read api_keys.json: {e}")
        return {}

def get_gemini_key() -> str | None:
    keys = load_api_keys()
    return keys.get("gemini_api_key")

def load_system_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ prompt.txt couldn't be loaded: {e}")
        return "You are CAS-E, a helpful Campus based emotion recognition robot."

SYSTEM_PROMPT = load_system_prompt()

def safe_json_parse(text: str) -> dict | None:
    if not text:
        return None
    text = text.strip()
    
    # Strip markdown code blocks if present
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.rindex("```")
            text = text[start:end].strip()
        except:
            pass
    elif "```" in text:
        try:
            start = text.index("```") + 3
            end = text.rindex("```")
            text = text[start:end].strip()
        except:
            pass

    try:
        # Final attempt to find the JSON braces
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"⚠️ Raw text preview: {text[:200]}")
        return None

def get_llm_output(user_text: str, memory_block: dict | None = None) -> dict:
    if not user_text or not user_text.strip():
        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": "Sir, I didn't catch that.",
            "memory_update": None
        }

    api_key = get_gemini_key()
    if not api_key:
        print("❌ GEMINI API KEY NOT FOUND")
        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": "Gemini API key is missing, Sir.",
            "memory_update": None
        }

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ GEMINI CLIENT INIT ERROR: {e}")
        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": "Gemini client could not be initialized.",
            "memory_update": None
        }

    generation_config = {
        "temperature": 0.2,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 1024,
    }

    memory_str = ""
    if memory_block:
        memory_str = "\n".join(f"{k}: {v}" for k, v in memory_block.items())

    user_prompt = f"""User message: "{user_text}"

Known user memory:
{memory_str if memory_str else "No memory available"}"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=user_prompt,
            config=generation_config
        )
        content = response.text

        parsed = safe_json_parse(content)

        if parsed:
            return {
                "intent": parsed.get("intent", "chat"),
                "parameters": parsed.get("parameters", {}),
                "needs_clarification": parsed.get("needs_clarification", False),
                "text": parsed.get("text"),
                "memory_update": parsed.get("memory_update")
            }

        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": content,
            "memory_update": None
        }

    except Exception as e:
        print(f"❌ GEMINI LLM ERROR: {e}")
        return {
            "intent": "chat",
            "parameters": {},
            "needs_clarification": False,
            "text": "Sir, a system error occurred with the Gemini engine.",
            "memory_update": None
        }
