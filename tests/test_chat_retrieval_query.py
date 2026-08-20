from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from chat.service.chat_service import rag_chat


def test_rag_chat_uses_rewritten_query_for_retrieval():
    model = RunnableLambda(lambda _: "测试回答")

    with (
        patch(
            "chat.service.chat_service.retrieve_and_rerank",
            return_value=[],
        ) as retrieve_mock,
        patch(
            "chat.service.chat_service.load_chat_model",
            return_value=model,
        ),
    ):
        answer = rag_chat(
            question="那我现在应该怎么做？",
            history="用户：公司的年假制度是什么？",
            retrieval_query=(
                "根据公司的年假制度，员工应如何申请年假？"
            ),
        )

    assert answer == "测试回答"
    retrieve_mock.assert_called_once_with(
        "根据公司的年假制度，员工应如何申请年假？"
    )


def test_rag_chat_falls_back_to_original_question():
    model = RunnableLambda(lambda _: "测试回答")

    with (
        patch(
            "chat.service.chat_service.retrieve_and_rerank",
            return_value=[],
        ) as retrieve_mock,
        patch(
            "chat.service.chat_service.load_chat_model",
            return_value=model,
        ),
    ):
        rag_chat(
            question="公司的请假制度是什么？",
            retrieval_query="   ",
        )

    retrieve_mock.assert_called_once_with(
        "公司的请假制度是什么？"
    )


if __name__ == "__main__":
    test_rag_chat_uses_rewritten_query_for_retrieval()
    test_rag_chat_falls_back_to_original_question()
    print("RAG 检索查询传递测试通过")
