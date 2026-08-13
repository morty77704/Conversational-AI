from functools import lru_cache

from langchain_chroma import Chroma

from ai.load_embedding_model import load_embedding_model
from common.config import get_settings


@lru_cache
def load_chroma() -> Chroma:
    settings = get_settings()

    if not settings.chroma_path.exists():
        raise FileNotFoundError(
            f"Chroma 目录不存在：{settings.chroma_path}"
        )

    database_file = settings.chroma_path / "chroma.sqlite3"

    if not database_file.exists():
        raise FileNotFoundError(
            f"Chroma 数据库文件不存在：{database_file}"
        )

    return Chroma(
        collection_name=settings.collection_name,
        persist_directory=str(settings.chroma_path),
        embedding_function=load_embedding_model(),
    )


def get_collection_info() -> dict[str, object]:
    vector_store = load_chroma()

    return {
        "name": vector_store._collection.name,
        "count": vector_store._collection.count(),
    }


