from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from create.build_documents import INGEST_BATCH, build_source_documents
from create.chunking import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    split_documents,
)


@dataclass(frozen=True)
class BuildResult:
    source_count: int
    chunk_count: int
    chunk_ids: list[str]


def build_chunks(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
):
    source_documents = build_source_documents()
    chunks, chunk_ids = split_documents(
        documents=source_documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return source_documents, chunks, chunk_ids


def replace_ingest_batch(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict[str, object]:
    # 干跑不需要导入模型相关组件，只有显式写库时才加载。
    from ai.load_chroma import load_chroma

    source_documents, chunks, chunk_ids = build_chunks(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    vector_store = load_chroma()
    collection = vector_store._collection
    count_before = collection.count()
    existing_data = collection.get(
        where={"ingest_batch": INGEST_BATCH},
        include=[],
    )
    existing_ids = existing_data.get("ids") or []

    # 只替换本脚本以前写入的同批数据，不触碰原知识库的其他切片。
    if existing_ids:
        collection.delete(ids=existing_ids)

    vector_store.add_documents(
        documents=chunks,
        ids=chunk_ids,
    )
    stored_data = collection.get(
        where={"ingest_batch": INGEST_BATCH},
        include=["metadatas"],
    )
    stored_ids = stored_data.get("ids") or []
    count_after = collection.count()

    if set(stored_ids) != set(chunk_ids):
        raise RuntimeError("Chroma 中的本批切片 ID 与预期不一致")

    return {
        "collection": collection.name,
        "sources": len(source_documents),
        "chunks": len(chunks),
        "replaced_chunks": len(existing_ids),
        "count_before": count_before,
        "count_after": count_after,
        "ingest_batch": INGEST_BATCH,
    }


def print_preview(chunk_size: int, chunk_overlap: int) -> BuildResult:
    source_documents, chunks, chunk_ids = build_chunks(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    print(f"源文档数：{len(source_documents)}")
    print(f"切片数：{len(chunks)}")

    for chunk in chunks:
        print(
            f"{chunk.id} | {chunk.metadata.get('doc_id')} | "
            f"{chunk.metadata.get('section_title')} | {len(chunk.page_content)} 字"
        )

    return BuildResult(
        source_count=len(source_documents),
        chunk_count=len(chunks),
        chunk_ids=chunk_ids,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建并写入示例制度知识库")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="只解析和切块，不写数据库")
    action.add_argument("--write", action="store_true", help="替换本批数据并写入 Chroma")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    return parser.parse_args()


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        # Codex/PowerShell 可能仍使用 GBK 代码页，显式输出 UTF-8 避免中文预览乱码。
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    if args.dry_run:
        print_preview(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        return

    result = replace_ingest_batch(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
