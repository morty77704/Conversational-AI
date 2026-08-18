from __future__ import annotations

import json
from pathlib import Path

from langchain_core.documents import Document

from create.document_loader import load_document

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
CATALOG_PATH = DATA_DIR / "source_catalog.json"
INGEST_BATCH = "abc-policy-demo-2026-08"


def load_catalog(catalog_path: Path = CATALOG_PATH) -> list[dict[str, object]]:
    raw_data = json.loads(catalog_path.read_text(encoding="utf-8"))
    documents = raw_data.get("documents")

    if not isinstance(documents, list) or not documents:
        raise ValueError("source_catalog.json 中没有 documents")

    return documents


def normalize_metadata(metadata: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}

    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            normalized[key] = value
        elif value is None:
            normalized[key] = ""
        else:
            # Chroma metadata 只接受标量，列表等结构统一保存为 JSON 字符串。
            normalized[key] = json.dumps(value, ensure_ascii=False)

    return normalized


def build_source_documents(
    catalog_path: Path = CATALOG_PATH,
) -> list[Document]:
    documents: list[Document] = []

    for item in load_catalog(catalog_path):
        relative_path = str(item.get("file", "")).strip()
        metadata = item.get("metadata")

        if not relative_path:
            raise ValueError("目录项缺少 file")

        if not isinstance(metadata, dict):
            raise ValueError(f"目录项缺少 metadata：{relative_path}")

        source_path = (catalog_path.parent / relative_path).resolve()
        merged_metadata = dict(metadata)
        merged_metadata.update(
            {
                "ingest_batch": INGEST_BATCH,
                "file_path": str(source_path),
                "format": source_path.suffix.lower().removeprefix("."),
                "embedding_model": "bge-base-zh-v1.5",
                "language": "zh-CN",
                "status": "active",
            }
        )
        merged_metadata.setdefault(
            "document_version_key",
            f"{merged_metadata.get('doc_id')}:{merged_metadata.get('version')}",
        )
        documents.append(
            load_document(
                path=source_path,
                metadata=normalize_metadata(merged_metadata),
            )
        )

    return documents

