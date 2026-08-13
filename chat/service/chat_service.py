from langchain_core.output_parsers import StrOutputParser
from collections.abc import Iterator

from ai.load_chat_model import load_chat_model
from chat.service.prompt_service import (
    build_context,
    general_chat_prompt,
    rag_prompt,
)
from chat.service.retrieval_service import retrieve_and_rerank


def general_chat(
        question: str,
        history: str = "",
) -> str:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("问题不能为空")

    chain = (
            general_chat_prompt
            | load_chat_model()
            | StrOutputParser()
    )

    return chain.invoke(
        {
            "history": history.strip() or "无",
            "question": cleaned_question,
        }
    )


def rag_chat(
        question: str,
        history: str = "",
) -> str:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("问题不能为空")

    ranked_documents = retrieve_and_rerank(
        cleaned_question
    )
    context = build_context(ranked_documents)

    chain = (
            rag_prompt
            | load_chat_model()
            | StrOutputParser()
    )

    return chain.invoke(
        {
            "history": history.strip() or "无",
            "context": context or "无可用资料",
            "question": cleaned_question,
        }
    )


def stream_general_chat(
        question: str,
        history: str = "",
) -> Iterator[str]:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("问题不能为空")

    chain = (
            general_chat_prompt
            | load_chat_model()
            | StrOutputParser()
    )

    for chunk in chain.stream(
            {
                "history": history.strip() or "无",
                "question": cleaned_question,
            }
    ):
        if chunk:
            yield chunk


def stream_rag_chat(
        question: str,
        history: str = "",
) -> Iterator[str]:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("问题不能为空")

    ranked_documents = retrieve_and_rerank(
        cleaned_question
    )
    context = build_context(ranked_documents)

    chain = (
            rag_prompt
            | load_chat_model()
            | StrOutputParser()
    )

    for chunk in chain.stream(
            {
                "history": history.strip() or "无",
                "context": context or "无可用资料",
                "question": cleaned_question,
            }
    ):
        if chunk:
            yield chunk


if __name__ == "__main__":
    # for chunk in stream_general_chat(
    #     "你好，请简单介绍一下自己"
    # ):
    #     print(chunk, end="", flush=True)
    for chunk in stream_rag_chat(
            "ABC-HR-PDF-0020 的适用范围和负责人是什么？"
    ):
        print(chunk, end="", flush=True)
