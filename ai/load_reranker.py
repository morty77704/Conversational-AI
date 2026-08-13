from functools import lru_cache

from FlagEmbedding import FlagReranker

from common.config import get_settings


@lru_cache
def load_reranker_model() -> FlagReranker:
    settings = get_settings()

    if not settings.reranker_model_path.exists():
        raise FileNotFoundError(
            "reranker 模型目录不存在："
            f"{settings.reranker_model_path}"
        )

    return FlagReranker(
        model_name_or_path=str(
            settings.reranker_model_path
        ),
        use_fp16=settings.reranker_use_fp16,
        devices=settings.reranker_device,
        batch_size=settings.reranker_batch_size,
        max_length=settings.reranker_max_length,
    )