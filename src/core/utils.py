"""
Lab 11 — Helper Utilities
"""
import asyncio

from google.genai import types

# Retry config — LLM providers (Gemini free tier especially) rate-limit quickly,
# so wrap every call in a bounded exponential backoff.
MAX_RETRIES = 4
BASE_DELAY = 2.0


async def chat_with_agent(agent, runner, user_message: str, session_id=None):
    """Send a message to the agent and get the response (with retry/backoff).

    Args:
        agent: The LlmAgent instance
        runner: The InMemoryRunner instance
        user_message: Plain text message to send
        session_id: Optional session ID to continue a conversation

    Returns:
        Tuple of (response_text, session)
    """
    user_id = "student"
    app_name = runner.app_name

    session = None
    if session_id is not None:
        try:
            session = await runner.session_service.get_session(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
        except (ValueError, KeyError):
            pass

    if session is None:
        session = await runner.session_service.create_session(
            app_name=app_name, user_id=user_id
        )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            final_response = ""
            async for event in runner.run_async(
                user_id=user_id, session_id=session.id, new_message=content
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_response += part.text
            return final_response, session
        except Exception as e:
            # Retry on transient errors (rate limit / 429 / 5xx / timeouts).
            last_err = e
            delay = BASE_DELAY * (2 ** attempt)
            print(f"  [retry {attempt + 1}/{MAX_RETRIES}] LLM call failed "
                  f"({type(e).__name__}); waiting {delay:.0f}s...")
            await asyncio.sleep(delay)

    raise last_err
