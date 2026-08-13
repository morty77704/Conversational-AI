from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from common.config import get_settings


@lru_cache
def load_embedding_model() -> HuggingFaceEmbeddings:
    settings = get_settings()

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={
            "device": settings.embedding_device,
            "local_files_only": True,
        },
        encode_kwargs={
            "normalize_embeddings": settings.embedding_normalize,
        },
    )


def encode_query(query: str) -> list[float]:
    settings = get_settings()
    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("查询文本不能为空")

    query_with_prefix = (
        f"{settings.embedding_query_prefix}{cleaned_query}"
    )

    model = load_embedding_model()
    vector = model.embed_query(query_with_prefix)

    if len(vector) != settings.embedding_expected_dimension:
        raise ValueError(
            "Embedding 向量维度与现有 Chroma 不兼容："
            f"实际 {len(vector)}，"
            f"预期 {settings.embedding_expected_dimension}"
        )

    return vector
