"""One model factory shared by the chat agent and structured trip planner."""

from langchain_deepseek import ChatDeepSeek
from ..config import Settings


def get_llm(settings: Settings) -> ChatDeepSeek:
    return ChatDeepSeek(
        model=settings.llm_model_id,
        api_key=settings.llm_api_key,
        api_base=settings.llm_base_url,
        timeout=settings.llm_timeout,
        max_retries=1,
        max_tokens=16000,
        # Explicitly keep the first implementation non-thinking. Tool message handling
        # is easier to inspect; switching modes requires separate integration testing.
        extra_body={'thinking': {'type': 'disabled'}},
    )
