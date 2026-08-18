from __future__ import annotations

import hashlib
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 450
DEFAULT_CHUNK_OVERLAP = 60
HEADING_PATTERN = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_PATTERN.finditer(text))

    if not matches:
        return [("正文", text.strip())]

    sections: list[tuple[str, str]] = []
    prefix = text[:matches[0].start()].strip()

    if prefix:
        sections.append(("文档说明", prefix))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(2).strip()
        section_text = text[start:end].strip()

        if section_text:
            sections.append((title, section_text))

    return sections


def create_chunk_id(
    doc_id: str,
    section_index: int,
    section_chunk_index: int,
) -> str:
    raw_id = f"{doc_id}:section:{section_index}:chunk:{section_chunk_index}"
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16]
    return f"policy-{doc_id.lower()}-{section_index:03d}-{section_chunk_index:03d}-{digest}"


def split_documents(
    documents: list[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> tuple[list[Document], list[str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须大于等于 0 且小于 chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " "],
        length_function=len,
    )
    chunks: list[Document] = []
    chunk_ids: list[str] = []

    for document in documents:
        doc_id = str(document.metadata.get("doc_id", "")).strip()

        if not doc_id:
            raise ValueError("每份源文档都必须包含 doc_id")

        global_chunk_index = 0

        for section_index, (section_title, section_text) in enumerate(
            split_markdown_sections(document.page_content)
        ):
            section_chunks = splitter.split_text(section_text)

            for section_chunk_index, content in enumerate(section_chunks):
                chunk_id = create_chunk_id(
                    doc_id=doc_id,
                    section_index=section_index,
                    section_chunk_index=section_chunk_index,
                )
                metadata = dict(document.metadata)
                metadata.update(
                    {
                        "chunk_index": global_chunk_index,
                        "section_index": section_index,
                        "section_chunk_index": section_chunk_index,
                        "section_title": section_title,
                        "source_location": section_title,
                        "content_hash": hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest(),
                    }
                )
                chunks.append(
                    Document(
                        id=chunk_id,
                        page_content=content,
                        metadata=metadata,
                    )
                )
                chunk_ids.append(chunk_id)
                global_chunk_index += 1

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("生成了重复的切片 ID")

    return chunks, chunk_ids

