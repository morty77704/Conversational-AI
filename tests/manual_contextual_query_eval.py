import argparse
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen

from common.config import get_settings
from chat.entity.intent_entity import IntentType
from chat.service.contextual_query_service import (
    analyze_contextual_query,
)
from chat.service.retrieval_service import retrieve_and_rerank


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    history: str
    question: str
    expected_intent: IntentType
    expected_context_sufficient: bool
    required_terms: tuple[str, ...] = ()
    forbidden_terms: tuple[str, ...] = ()
    expected_doc_ids: tuple[str, ...] = ()


CASES = (
    EvaluationCase(
        name="年假追问",
        history=(
            "用户：公司的年假申请流程是什么？\n"
            "助手：年假需要按照公司规定提交申请。\n"
            "用户：我已经工作两年了。"
        ),
        question="那我现在应该怎么做？",
        expected_intent=IntentType.KNOWLEDGE_QUERY,
        expected_context_sufficient=True,
        required_terms=("年假",),
        forbidden_terms=("病假", "产假", "报销"),
        expected_doc_ids=("ABC-HR-PDF-0020",),
    ),
    EvaluationCase(
        name="病假材料追问",
        history=(
            "用户：我想了解公司的病假规定。\n"
            "助手：需要根据病假制度确认申请条件。"
        ),
        question="那需要准备什么材料？",
        expected_intent=IntentType.KNOWLEDGE_QUERY,
        expected_context_sufficient=True,
        required_terms=("病假", "材料"),
        forbidden_terms=("年假", "产假", "报销"),
    ),
    EvaluationCase(
        name="最近话题优先",
        history=(
            "用户：公司的请假制度是什么？\n"
            "助手：请假需要按规定申请。\n"
            "用户：另外，出差报销需要哪些材料？\n"
            "助手：需要依据公司的报销规定确认。"
        ),
        question="那具体应该怎么提交？",
        expected_intent=IntentType.KNOWLEDGE_QUERY,
        expected_context_sufficient=True,
        required_terms=("报销",),
        forbidden_terms=("年假", "病假"),
    ),
    EvaluationCase(
        name="明确文档编号",
        history="暂无历史对话",
        question="ABC-HR-PDF-0020 讲了什么？",
        expected_intent=IntentType.KNOWLEDGE_QUERY,
        expected_context_sufficient=True,
        required_terms=("ABC-HR-PDF-0020",),
        expected_doc_ids=("ABC-HR-PDF-0020",),
    ),
    EvaluationCase(
        name="无历史的模糊追问",
        history="暂无历史对话",
        question="那我现在应该怎么做？",
        expected_intent=IntentType.UNCERTAIN,
        expected_context_sufficient=False,
    ),
    EvaluationCase(
        name="完整闲聊问题",
        history="暂无历史对话",
        question="你好，今天过得怎么样？",
        expected_intent=IntentType.GENERAL_CHAT,
        expected_context_sufficient=True,
    ),
)


def is_ollama_available() -> bool:
    settings = get_settings()
    tags_url = (
        settings.ollama_base_url.rstrip("/")
        + "/api/tags"
    )

    try:
        with urlopen(tags_url, timeout=2):
            return True
    except (OSError, URLError):
        return False


def evaluate_case(
        case: EvaluationCase,
        with_retrieval: bool,
) -> list[str]:
    failures: list[str] = []
    result = analyze_contextual_query(
        question=case.question,
        history=case.history,
    )

    if result.intent != case.expected_intent:
        failures.append(
            "意图不符："
            f"expected={case.expected_intent.value}, "
            f"actual={result.intent.value}"
        )

    if (
            result.context_sufficient
            != case.expected_context_sufficient
    ):
        failures.append(
            "上下文充分性不符："
            f"expected={case.expected_context_sufficient}, "
            f"actual={result.context_sufficient}"
        )

    for term in case.required_terms:
        if term.lower() not in result.standalone_query.lower():
            failures.append(f"缺少关键词：{term}")

    for term in case.forbidden_terms:
        if term.lower() in result.standalone_query.lower():
            failures.append(f"出现错误主题：{term}")

    retrieved_doc_ids: set[str] = set()

    if (
            with_retrieval
            and result.context_sufficient
            and result.intent == IntentType.KNOWLEDGE_QUERY
    ):
        documents = retrieve_and_rerank(
            result.standalone_query
        )
        retrieved_doc_ids = {
            str(document.metadata.get("doc_id", ""))
            for document, _ in documents
        }

        for doc_id in case.expected_doc_ids:
            if doc_id not in retrieved_doc_ids:
                failures.append(
                    f"Top-K 未召回预期文档：{doc_id}"
                )

    print(f"[{case.name}] {result.standalone_query}")
    print(
        "  intent="
        f"{result.intent.value}, "
        "context_sufficient="
        f"{result.context_sufficient}, "
        f"evidence={result.history_evidence}"
    )

    if with_retrieval and retrieved_doc_ids:
        print(f"  retrieved_doc_ids={sorted(retrieved_doc_ids)}")

    if failures:
        for failure in failures:
            print(f"  FAIL: {failure}")
    else:
        print("  PASS")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="手动评估上下文查询改写质量"
    )
    parser.add_argument(
        "--with-retrieval",
        action="store_true",
        help="额外执行只读检索和预期文档 Recall 检查",
    )
    args = parser.parse_args()

    if not is_ollama_available():
        print(
            "Ollama 当前不可用，无法评估真实模型改写质量；"
            "请启动本地 Ollama 后重试。"
        )
        return 2

    all_failures: dict[str, list[str]] = {}

    for case in CASES:
        failures = evaluate_case(
            case=case,
            with_retrieval=args.with_retrieval,
        )

        if failures:
            all_failures[case.name] = failures

    print(
        f"完成 {len(CASES)} 条评测，"
        f"失败 {len(all_failures)} 条。"
    )

    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
