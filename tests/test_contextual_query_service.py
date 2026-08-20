from unittest.mock import patch

from chat.entity.contextual_query_entity import (
    ContextualQueryResult,
)
from chat.entity.intent_entity import IntentType
from chat.service.contextual_query_service import (
    analyze_contextual_query,
    validate_contextual_query,
)


def build_result(
        standalone_query: str,
        *,
        intent: IntentType = IntentType.KNOWLEDGE_QUERY,
        context_sufficient: bool = True,
        rewrite_needed: bool = True,
        history_evidence: list[str] | None = None,
) -> ContextualQueryResult:
    return ContextualQueryResult(
        intent=intent,
        standalone_query=standalone_query,
        context_sufficient=context_sufficient,
        rewrite_needed=rewrite_needed,
        history_evidence=history_evidence or [],
    )


def test_valid_contextual_query_passes_validation():
    history = (
        "用户：公司的年假申请流程是什么？\n"
        "用户：我已经工作两年了。"
    )
    result = build_result(
        "根据公司的年假申请流程，工作两年的员工"
        "现在应该如何申请年假？",
        history_evidence=[
            "公司的年假申请流程",
            "工作两年",
        ],
    )

    errors = validate_contextual_query(
        question="那我现在应该怎么做？",
        history=history,
        result=result,
    )

    assert errors == []


def test_validation_detects_missing_document_id_and_number():
    result = build_result(
        "该制度是否适用于实习生？",
        rewrite_needed=False,
    )

    errors = validate_contextual_query(
        question=(
            "ABC-HR-PDF-0020 中工作满3年的规定"
            "适用于实习生吗？"
        ),
        history="暂无历史对话",
        result=result,
    )

    assert any("遗漏当前问题中的文档编号" in error for error in errors)
    assert any("遗漏当前问题中的数字限制" in error for error in errors)


def test_validation_detects_untraceable_evidence_and_topic():
    result = build_result(
        "根据公司的产假制度，我现在应该怎么办？",
        history_evidence=["公司的产假制度"],
    )

    errors = validate_contextual_query(
        question="那我现在应该怎么办？",
        history="用户：刚才讨论的是病假申请。",
        result=result,
    )

    assert any("业务主题：产假" in error for error in errors)
    assert any("历史依据无法在原文中找到" in error for error in errors)


def test_validation_detects_lost_person_department_and_negation():
    result = build_result(
        "员工可以向负责人申请吗？",
        rewrite_needed=False,
    )

    errors = validate_contextual_query(
        question="财务部实习生不能直接申请吗？",
        history="暂无历史对话",
        result=result,
    )

    assert any(
        "人员、部门或否定限制" in error
        and "财务部" in error
        and "实习生" in error
        and "不能" in error
        for error in errors
    )


def test_analysis_retries_once_after_validation_failure():
    invalid_result = build_result(
        "根据公司的产假制度，我现在应该怎么办？",
        history_evidence=["公司的病假制度"],
    )
    valid_result = build_result(
        "根据公司的病假制度，我现在应该怎么办？",
        history_evidence=["公司的病假制度"],
    )

    with (
        patch(
            "chat.service.contextual_query_service."
            "_invoke_contextual_query_model",
            side_effect=[invalid_result, valid_result],
        ) as invoke_mock,
        patch(
            "chat.service.contextual_query_service.logger.warning",
        ),
    ):
        result = analyze_contextual_query(
            question="那我现在应该怎么办？",
            history="用户：公司的病假制度是什么？",
        )

    assert result == valid_result
    assert invoke_mock.call_count == 2
    assert invoke_mock.call_args_list[1].kwargs[
        "validation_errors"
    ]


def test_analysis_falls_back_after_two_invalid_results():
    invalid_result = build_result(
        "根据公司的产假制度，我现在应该怎么办？",
        history_evidence=["公司的病假制度"],
    )

    with (
        patch(
            "chat.service.contextual_query_service."
            "_invoke_contextual_query_model",
            side_effect=[invalid_result, invalid_result],
        ) as invoke_mock,
        patch(
            "chat.service.contextual_query_service.logger.warning",
        ),
    ):
        result = analyze_contextual_query(
            question="那我现在应该怎么办？",
            history="用户：公司的病假制度是什么？",
        )

    assert invoke_mock.call_count == 2
    assert result.intent == IntentType.UNCERTAIN
    assert result.context_sufficient is False
    assert result.standalone_query == "那我现在应该怎么办？"


def test_context_insufficient_result_does_not_retry():
    insufficient_result = build_result(
        "那我现在应该怎么办？",
        intent=IntentType.UNCERTAIN,
        context_sufficient=False,
        rewrite_needed=True,
    )

    with patch(
        "chat.service.contextual_query_service."
        "_invoke_contextual_query_model",
        return_value=insufficient_result,
    ) as invoke_mock:
        result = analyze_contextual_query(
            question="那我现在应该怎么办？",
            history="暂无历史对话",
        )

    assert result == insufficient_result
    invoke_mock.assert_called_once()


def test_model_failure_keeps_complete_knowledge_question():
    with (
        patch(
            "chat.service.contextual_query_service."
            "_invoke_contextual_query_model",
            side_effect=RuntimeError("mock model error"),
        ),
        patch(
            "chat.service.contextual_query_service.logger.exception",
        ),
    ):
        result = analyze_contextual_query(
            question="公司的请假制度是什么？",
            history="暂无历史对话",
        )

    assert result.intent == IntentType.KNOWLEDGE_QUERY
    assert result.context_sufficient is True
    assert result.rewrite_needed is False
    assert result.standalone_query == "公司的请假制度是什么？"


def test_model_failure_rejects_other_ambiguous_follow_ups():
    questions = (
        "那需要准备什么材料？",
        "那具体应该怎么提交？",
        "这个可以吗？",
    )

    with (
        patch(
            "chat.service.contextual_query_service."
            "_invoke_contextual_query_model",
            side_effect=RuntimeError("mock model error"),
        ),
        patch(
            "chat.service.contextual_query_service.logger.exception",
        ),
    ):
        results = [
            analyze_contextual_query(
                question=question,
                history="用户：正在讨论一项公司制度。",
            )
            for question in questions
        ]

    assert all(
        result.context_sufficient is False
        for result in results
    )


if __name__ == "__main__":
    test_valid_contextual_query_passes_validation()
    test_validation_detects_missing_document_id_and_number()
    test_validation_detects_untraceable_evidence_and_topic()
    test_validation_detects_lost_person_department_and_negation()
    test_analysis_retries_once_after_validation_failure()
    test_analysis_falls_back_after_two_invalid_results()
    test_context_insufficient_result_does_not_retry()
    test_model_failure_keeps_complete_knowledge_question()
    test_model_failure_rejects_other_ambiguous_follow_ups()
    print("上下文查询服务测试通过")
