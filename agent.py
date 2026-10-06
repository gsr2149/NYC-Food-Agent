"""Gemini chat loop with manual tool calling and per-session memory."""

import os

from google import genai
from google.genai import types

from tools import TOOLS

SYSTEM_PROMPT = """You are Bite Buddy, an NYC food-finding assistant for young,
indecisive diners. Before searching, find out (one short question at a time):
cuisine, borough, price point, and where the user is starting from.
If the user can't decide, use suggest_cuisines or surprise_pick.
Keep answers short and friendly. Never invent restaurants; only recommend
ones returned by your tools. If a tool returns an error, follow its advice."""

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_ROUNDS = 6

_client = None
_sessions: dict[str, "genai.chats.Chat"] = {}  # session_id -> chat (in memory)


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY from the environment
    return _client


def _get_chat(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = _get_client().chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=list(TOOLS.values()),
                # We run tools ourselves so we can record every call.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
    return _sessions[session_id]


def run_turn(session_id: str, message: str) -> tuple[str, list[dict]]:
    """Send one user message; return (reply_text, tool_calls)."""
    chat = _get_chat(session_id)
    tool_calls: list[dict] = []
    response = chat.send_message(message)

    for _ in range(MAX_TOOL_ROUNDS):
        calls = response.function_calls or []
        if not calls:
            break
        parts = []
        for call in calls:
            args = dict(call.args or {})
            fn = TOOLS.get(call.name)
            try:
                result = fn(**args) if fn else {"error": f"Unknown tool {call.name}"}
            except Exception as e:  # last-resort guard; tools should return errors
                result = {"error": f"{type(e).__name__}: {e}"}
            tool_calls.append({"name": call.name, "args": args, "result": result})
            parts.append(types.Part.from_function_response(name=call.name, response=result))
        response = chat.send_message(parts)

    return response.text or "", tool_calls
