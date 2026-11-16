
import asyncio
import os
import re

from dotenv import load_dotenv
from getpatter import Patter, Telnyx, OpenAIRealtime2, tool

from memory import (
    initialize_memory,
    save_message,
    get_memory_context,
    get_facts,
    get_projects,
    get_tasks,
    remember_fact
)

from memory_ai import process_user_message

load_dotenv()


# ==========================================
# PHONE EVENTS
# ==========================================

async def call_started(data):
    print("CALL STARTED:", data)
    return {}


async def call_ended(data):
    print("CALL ENDED")


# ==========================================
# CONVERSATION MEMORY
# ==========================================

async def transcript_received(data):
    print("TRANSCRIPT RECEIVED:", data)

    if isinstance(data, dict):
        role = data.get("role", "unknown")
        content = data.get("text", "")
    else:
        role = getattr(data, "role", "unknown")
        content = getattr(data, "text", "")

    if content:
        save_message(str(role), str(content))
        print("SAVED TO JARVIS MEMORY")

        if str(role).lower() == "user":
            print("AI MEMORY PROCESSING...")

            await asyncio.to_thread(
                process_user_message,
                str(content)
            )


# ==========================================
# LIVE MEMORY SEARCH
# ==========================================

@tool
async def search_jarvis_memory(query: str) -> dict:
    """Search saved personal facts, interests, projects and tasks."""

    query = query.strip().lower()

    terms = [
        word for word in query.split()
        if len(word) > 2
    ]

    facts = get_facts()
    projects = get_projects()
    tasks = get_tasks()

    matching_facts = [
        {"key": key, "value": value}
        for key, value in facts
        if not terms or any(
            term in key.lower() or term in value.lower()
            for term in terms
        )
    ]

    if not matching_facts:
        matching_facts = [
            {"key": key, "value": value}
            for key, value in facts
        ]

    matching_projects = [
        {
            "title": p[1],
            "details": p[2],
            "status": p[3]
        }
        for p in projects
        if not terms or any(
            term in f"{p[1]} {p[2]} {p[3]}".lower()
            for term in terms
        )
    ]

    matching_tasks = [
        {
            "title": t[1],
            "details": t[2],
            "status": t[3],
            "project": t[4]
        }
        for t in tasks
        if not terms or any(
            term in f"{t[1]} {t[2]} {t[3]} {t[4]}".lower()
            for term in terms
        )
    ]

    print("JARVIS LIVE MEMORY SEARCH:", query)

    return {
        "query": query,
        "facts": matching_facts[:50],
        "projects": matching_projects[:50],
        "tasks": matching_tasks[:50]
    }


# ==========================================
# LIVE MEMORY SAVING
# ==========================================

@tool
async def save_jarvis_memory(
    key: str,
    value: str,
    category: str = "general"
) -> dict:
    """
    Save or update a personal fact immediately in Jarvis's database.
    Use when the user explicitly asks you to remember something.
    """

    key = key.strip().lower()
    value = value.strip()
    category = category.strip().lower()

    if not re.fullmatch(r"[a-z0-9_]{1,60}", key):
        return {"success": False, "error": "Invalid memory key."}

    if key == "system":
        return {"success": False, "error": "Reserved memory key."}

    if not value or len(value) > 500:
        return {"success": False, "error": "Invalid memory value."}

    if not category or len(category) > 40:
        return {"success": False, "error": "Invalid category."}

    remember_fact(key, value, category)

    print("JARVIS LIVE MEMORY SAVED:", key, "=", value)

    return {
        "success": True,
        "key": key,
        "value": value,
        "category": category
    }


# ==========================================
# MAIN JARVIS SYSTEM
# ==========================================

async def main():

    initialize_memory()
    print("JARVIS MEMORY INITIALIZED")

    memory_context = get_memory_context()

    phone = Patter(
        carrier=Telnyx(),
        phone_number=os.environ["TELNYX_PHONE_NUMBER"],
        webhook_url="mindful-harmony-production-08878ac5.up.railway.app"
    )

    agent = phone.agent(
        engine=OpenAIRealtime2(),

        system_prompt=f"""
You are Jarvis, a personal AI assistant.

Speak naturally, intelligently, and clearly.
Be helpful, concise, and conversational.

PERSISTENT MEMORY:

{memory_context}

MEMORY INSTRUCTIONS:

1. You have two memory tools:
   - search_jarvis_memory
   - save_jarvis_memory

2. Use search_jarvis_memory whenever the user asks
   what you remember or asks about saved information.

3. Use save_jarvis_memory when the user explicitly
   asks you to remember or save a personal fact.

4. Choose a descriptive key for each fact.
   Example: favorite_food, hobby_fishing, favorite_color.

5. If a fact with the same key already exists,
   update it rather than creating another key.

6. After saving, check that the tool returned
   success before confirming it to the user.

7. You can search for a newly saved fact immediately
   during the same phone call.

8. Never invent memories or claim a save succeeded
   when the tool reports an error.

9. Automatic memory extraction also runs in the
   background when the user speaks.

GENERAL INSTRUCTIONS:

Speak conversationally and naturally.

Never claim you completed an action unless you
actually have the tools and confirmation to do it.

You cannot execute trades or publish social media
posts yet.
""",

        first_message="Hello. Jarvis is online. How can I help?",

        voice="cedar",

        tools=[
            search_jarvis_memory,
            save_jarvis_memory
        ]
    )

    print("JARVIS VOICE SYSTEM STARTING...")

    await phone.serve(
        agent,
            port=int(os.getenv("PORT", "8000")),
        tunnel=False,
        dashboard=False,
        on_call_start=call_started,
        on_call_end=call_ended,
        on_transcript=transcript_received
    )


if __name__ == "__main__":
    asyncio.run(main())
