from functools import lru_cache

from langchain_openai import ChatOpenAI

from common.config import get_settings


@lru_cache
def load_chat_model() -> ChatOpenAI:
    settings = get_settings()

    if not settings.llm_api_key.strip():
        raise ValueError("LLM_API_KEY 未配置")

    if not settings.llm_base_url.strip():
        raise ValueError("LLM_BASE_URL 未配置")

    if not settings.llm_model.strip():
        raise ValueError("LLM_MODEL 未配置")

    return ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        streaming=True,
    )