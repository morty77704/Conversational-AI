import tempfile
import unittest
from pathlib import Path

from create.build_documents import INGEST_BATCH, build_source_documents
from create.chunking import split_documents
from create.document_loader import load_document


class CreatePolicyPipelineTest(unittest.TestCase):
    def test_load_utf8_text_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "sample.md"
            source_path.write_text(
                "# 标题\n\n第一段。\n\n\n第二段。",
                encoding="utf-8",
            )

            document = load_document(source_path, {"doc_id": "TEST-001"})

            self.assertEqual(
                document.page_content,
                "# 标题\n\n第一段。\n\n第二段。",
            )
            self.assertEqual(document.metadata["format"], "md")

    def test_policy_documents_have_required_metadata(self):
        documents = build_source_documents()

        self.assertEqual(len(documents), 6)

        for document in documents:
            self.assertTrue(document.metadata["doc_id"])
            self.assertTrue(document.metadata["title"])
            self.assertTrue(document.metadata["version"])
            self.assertEqual(document.metadata["ingest_batch"], INGEST_BATCH)

    def test_policy_chunks_are_stable_and_cover_three_questions(self):
        documents = build_source_documents()
        chunks, chunk_ids = split_documents(documents)
        repeated_chunks, repeated_ids = split_documents(documents)
        all_content = "\n".join(chunk.page_content for chunk in chunks)

        self.assertTrue(chunks)
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)))
        self.assertEqual(chunk_ids, repeated_ids)
        self.assertEqual(
            [chunk.page_content for chunk in chunks],
            [chunk.page_content for chunk in repeated_chunks],
        )

        self.assertIn(
            "转正申请表、试用期工作总结、试用期目标完成情况自评",
            all_content,
        )
        self.assertIn(
            "一线城市500元、重点城市400元、其他城市350元",
            all_content,
        )
        self.assertIn("飞机经济舱、高铁二等座", all_content)
        self.assertIn(
            "五天；满十年不满二十年的为十天；满二十年的为十五天",
            all_content,
        )
        self.assertIn("一个工作日内补办", all_content)


if __name__ == "__main__":
    unittest.main()

