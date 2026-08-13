import jieba
import re
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from functools import lru_cache

from ai.load_chroma import load_chroma

# 正则匹配数据编号防止bm25检索完整数据编号时，数据编号被拆分
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+", re.IGNORECASE, )


def tokenize(text: str) -> list[str]:
    if not text or not text.strip():
        return []

    normalized_text = text.lower()

    identifier_tokens = IDENTIFIER_PATTERN.findall(
        normalized_text
    )

    word_tokens = [
        token.strip()
        for token in jieba.lcut(normalized_text)
        if token.strip() and token.strip().isalnum()
    ]

    return identifier_tokens + word_tokens


class BM25Index:
    def __init__(
            self,
            documents: list[Document],
            tokenized_corpus: list[list[str]],
    ):
        self.documents = documents
        self.tokenized_corpus = tokenized_corpus
        self.bm25 = BM25Okapi(tokenized_corpus)


@lru_cache
def load_bm25_index() -> BM25Index:
    vector_store = load_chroma()

    collection_data = vector_store.get(
        include=["documents", "metadatas"],
    )

    document_ids = collection_data.get("ids") or []
    contents = collection_data.get("documents") or []
    metadatas = collection_data.get("metadatas") or []

    documents: list[Document] = []
    tokenized_corpus: list[list[str]] = []

    for index, content in enumerate(contents):
        if not content:
            continue

        tokens = tokenize(content)

        if not tokens:
            continue

        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        document_id = (
            document_ids[index]
            if index < len(document_ids)
            else None
        )

        documents.append(
            Document(
                id=document_id,
                page_content=content,
                metadata=metadata,
            )
        )
        tokenized_corpus.append(tokens)

    if not documents:
        raise ValueError("Chroma 中没有可用于构建 BM25 索引的文档")

    return BM25Index(
        documents=documents,
        tokenized_corpus=tokenized_corpus,
    )


if __name__ == '__main__':
    index = load_bm25_index()
    print('文档数：', len(index.documents))
    print('分词数：', len(index.tokenized_corpus))
    print('缓存：', index is load_bm25_index())
    print('示例分词：', index.tokenized_corpus[0][:20])
