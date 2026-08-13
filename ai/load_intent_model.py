from functools import lru_cache

from langchain_ollama import ChatOllama

from common.config import get_settings


@lru_cache
def load_intent_model() -> ChatOllama:
    settings = get_settings()

    return ChatOllama(
        model=settings.intent_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        reasoning=False,
        num_predict=64,
        keep_alive="30m",
    )