from langchain_core.documents import Document

from ai.load_chroma import load_chroma
from ai.load_embedding_model import encode_query
from ai.load_bm25 import load_bm25_index, tokenize
from ai.load_reranker import load_reranker_model
from common.config import get_settings

RRF_K = 60


def vector_search(
        query: str,
        top_k: int = 5,
) -> list[tuple[Document, float]]:
    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    query_vector = encode_query(query)
    vector_store = load_chroma()

    results = (
        vector_store
        .similarity_search_by_vector_with_relevance_scores(
            embedding=query_vector,
            k=top_k,
        )
    )

    return results


def bm25_search(
        query: str,
        top_k: int = 5,
) -> list[tuple[Document, float]]:
    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    bm25_index = load_bm25_index()
    scores = bm25_index.bm25.get_scores(query_tokens)

    ranked_items = sorted(
        enumerate(scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    results: list[tuple[Document, float]] = []

    for document_index, score in ranked_items:
        score = float(score)

        if score <= 0:
            continue

        results.append(
            (
                bm25_index.documents[document_index],
                score,
            )
        )

        if len(results) >= top_k:
            break

    return results


def get_document_key(document: Document) -> str:
    """获取稳定的切片标识，用于合并两路检索中的同一切片。"""
    if document.id:
        return str(document.id)

    content_hash = document.metadata.get("content_hash")

    if content_hash:
        return str(content_hash)

    return document.page_content


def reciprocal_rank_fusion(
        result_lists: list[list[Document]],
        rrf_k: int = RRF_K,
) -> list[tuple[Document, float]]:
    """只根据候选排名计算 RRF 分数并合并重复切片。"""
    if rrf_k <= 0:
        raise ValueError("rrf_k 必须大于 0")

    document_scores: dict[str, float] = {}
    document_mapping: dict[str, Document] = {}

    for documents in result_lists:
        # 同一路结果中的重复切片只计分一次。
        current_list_keys: set[str] = set()

        for rank, document in enumerate(documents, start=1):
            document_key = get_document_key(document)

            if document_key in current_list_keys:
                continue

            current_list_keys.add(document_key)
            document_mapping.setdefault(document_key, document)

            rrf_score = 1 / (rrf_k + rank)
            document_scores[document_key] = (
                    document_scores.get(document_key, 0.0)
                    + rrf_score
            )

    sorted_keys = sorted(
        document_scores,
        key=document_scores.get,
        reverse=True,
    )

    return [
        (
            document_mapping[document_key],
            document_scores[document_key],
        )
        for document_key in sorted_keys
    ]


def hybrid_search(
        query: str,
        vector_top_k: int = 10,
        bm25_top_k: int = 10,
        rrf_k: int = RRF_K,
) -> list[tuple[Document, float]]:
    """执行向量检索和 BM25 检索，再使用 RRF 融合候选。"""
    vector_results = vector_search(
        query=query,
        top_k=vector_top_k,
    )
    bm25_results = bm25_search(
        query=query,
        top_k=bm25_top_k,
    )

    return reciprocal_rank_fusion(
        result_lists=[
            [document for document, _ in vector_results],
            [document for document, _ in bm25_results],
        ],
        rrf_k=rrf_k,
    )


def rerank_documents(
        query: str,
        candidates: list[tuple[Document, float]],
        top_n: int | None = None,
) -> list[tuple[Document, float]]:
    cleaned_query = query.strip()

    if not cleaned_query:
        raise ValueError("查询文本不能为空")

    if not candidates:
        return []

    settings = get_settings()

    if top_n is None:
        top_n = settings.reranker_top_n

    if top_n <= 0:
        raise ValueError("top_n 必须大于 0")

    sentence_pairs = [
        (
            cleaned_query,
            document.page_content,
        )
        for document, _ in candidates
    ]

    reranker = load_reranker_model()
    scores = reranker.compute_score(sentence_pairs)

    # 只有一个候选时，FlagReranker 可能返回单个数字。
    if not isinstance(scores, (list, tuple)):
        scores = [scores]

    if len(scores) != len(candidates):
        raise ValueError(
            "reranker 返回的分数数量与候选数量不一致"
        )

    ranked_candidates = sorted(
        (
            (
                document,
                float(reranker_score),
                rrf_score,
            )
            for (
            document,
            rrf_score,
        ), reranker_score in zip(
            candidates,
            scores,
        )
        ),
        # reranker 分数相同时，使用 RRF 分数稳定排序。
        key=lambda item: (
            item[1],
            item[2],
        ),
        reverse=True,
    )

    return [
        (
            document,
            reranker_score,
        )
        for (
            document,
            reranker_score,
            _,
        ) in ranked_candidates[:top_n]
    ]


def retrieve_and_rerank(
        query: str,
        vector_top_k: int = 10,
        bm25_top_k: int = 10,
        top_n: int | None = None,
) -> list[tuple[Document, float]]:
    candidates = hybrid_search(
        query=query,
        vector_top_k=vector_top_k,
        bm25_top_k=bm25_top_k,
    )

    return rerank_documents(
        query=query,
        candidates=candidates,
        top_n=top_n,
    )


if __name__ == '__main__':
    # vector_results = vector_search("公司的请假制度是什么", 3)
    # print('数量：', len(vector_results))
    # for doc, score in vector_results:
    #     print('距离：', round(score, 4)),
    #     print('标题：', doc.metadata.get('title')),
    #     print('正文：', doc.page_content[:100])
    # bm25_results = bm25_search("公司的请假制度是什么", 3)
    # for doc, score in bm25_results:
    #     print(round(score, 4), doc.metadata.get('doc_id'), doc.metadata.get('title'))
    # bm25_results = bm25_search("ABC-HR-PDF-0020", 3)
    # for doc, score in bm25_results:
    #     print(round(score, 4), doc.metadata.get('doc_id'), doc.metadata.get('title'))
    results = retrieve_and_rerank('公司的请假制度是什么？')
    for i, (doc, score) in enumerate(results, 1):
        print('排名：', i, '分数：', round(score, 4),
              '编号：', doc.metadata.get('doc_id'),
              '标题：', doc.metadata.get('title'))
