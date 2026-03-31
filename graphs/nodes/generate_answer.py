"""
Generate Answer Node.
Converts SQL execution results into user-friendly natural language reports.
Handles all scenarios: success, failure, sandbox blocked, no SQL.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.llm_client import llm_client
from graphs.state import NL2SQLState
from graphs.nodes.generate_sql import load_prompt_template


def generate_answer_node(state: NL2SQLState) -> NL2SQLState:
    """
    Generate a natural language answer based on query results.

    Handles multiple scenarios:
    - Execution success with data
    - Execution success with no data
    - Execution failure
    - Sandbox blocked
    - No SQL generated
    """
    question = state.get("question", "")
    candidate_sql = state.get("candidate_sql")
    execution_result = state.get("execution_result")
    sandbox = state.get("sandbox")
    validation = state.get("validation")

    print(f"\n=== Generate Answer Node ===")
    print(f"Question: {question}")

    # Determine scenario and prepare inputs
    scenario, error, sandbox_blocked = _determine_scenario(
        candidate_sql, execution_result, sandbox
    )

    print(f"Scenario: {scenario}")

    # Format execution result for prompt
    execution_result_str = _format_execution_result(execution_result, scenario)

    # Load prompt template
    prompt_template = load_prompt_template("answer")

    # Format prompt
    prompt = prompt_template.format(
        question=question,
        candidate_sql=candidate_sql or "未生成 SQL",
        execution_result=execution_result_str,
        error=error or "无",
        sandbox_blocked="是" if sandbox_blocked else "否"
    )

    # Call LLM to generate answer
    try:
        response = llm_client.chat(prompt=prompt)
        print(f"\nGenerated Answer:\n{response}")

        return {
            **state,
            "answer": response,
            "answer_generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"\n✗ Error generating answer: {e}")
        fallback_answer = _generate_fallback_answer(question, scenario, error, sandbox_blocked)
        return {
            **state,
            "answer": fallback_answer,
            "answer_generated_at": datetime.now().isoformat()
        }


def _determine_scenario(candidate_sql, execution_result, sandbox):
    """
    Determine the current scenario based on state.

    Returns:
        tuple: (scenario_name, error_message, sandbox_blocked)
    """
    # Scenario D: Sandbox blocked
    if sandbox and not sandbox.get("is_safe", True):
        return ("sandbox_blocked", sandbox.get("blocked_reason", "安全拦截"), True)

    # Scenario: No SQL
    if not candidate_sql:
        return ("no_sql", "未生成 SQL 语句", False)

    # Scenario: No execution result (sandbox passed but execute_sql was skipped)
    if execution_result is None:
        return ("no_execution", "未执行查询", False)

    # Scenario B/C: Execution result exists
    if execution_result.get("ok"):
        if execution_result.get("row_count", 0) == 0:
            return ("empty_result", None, False)
        else:
            return ("success", None, False)
    else:
        return ("execution_error", execution_result.get("error", "未知错误"), False)


def _format_execution_result(execution_result, scenario):
    """
    Format execution result into a readable string for the prompt.
    """
    if not execution_result:
        return "无执行结果"

    if scenario == "sandbox_blocked":
        return "查询被安全系统拦截，未执行"

    if scenario == "no_sql":
        return "未生成 SQL 语句"

    if scenario == "execution_error":
        return f"执行失败：{execution_result.get('error', '未知错误')}"

    if scenario == "empty_result":
        return f"执行成功，但未找到数据（0 行）\n列名：{execution_result.get('columns', [])}"

    # Scenario: success
    rows = execution_result.get("rows", [])
    columns = execution_result.get("columns", [])
    row_count = execution_result.get("row_count", 0)

    result_str = f"执行成功，返回 {row_count} 行数据\n"
    result_str += f"列名：{columns}\n"

    # Show first few rows as sample
    sample_size = min(10, len(rows))
    if sample_size > 0:
        result_str += f"\n数据样例（前 {sample_size} 行）：\n"
        for i, row in enumerate(rows[:sample_size], 1):
            result_str += f"  行 {i}: {json.dumps(row, ensure_ascii=False, default=str)}\n"

    if row_count > sample_size:
        result_str += f"\n... 还有 {row_count - sample_size} 行数据未显示"

    return result_str


def _generate_fallback_answer(question, scenario, error, sandbox_blocked):
    """
    Generate a fallback answer when LLM call fails.
    """
    if sandbox_blocked:
        return (
            f"⚠️ 安全警告\n\n"
            f"您的查询已被安全系统拦截。\n"
            f"原因：{error}\n\n"
            f"本系统仅允许只读查询（SELECT），以确保数据安全。\n"
            f"请尝试提出其他查询需求。"
        )
    elif scenario == "no_sql":
        return (
            f"抱歉，系统未能生成有效的 SQL 查询。\n\n"
            f"问题：{question}\n"
            f"请尝试用更明确的方式重新描述您的需求。"
        )
    elif scenario == "execution_error":
        return (
            f"查询执行失败。\n\n"
            f"问题：{question}\n"
            f"错误信息：{error}\n\n"
            f"请尝试重新提问或联系管理员。"
        )
    elif scenario == "empty_result":
        return (
            f"查询执行成功，但未找到匹配的数据。\n\n"
            f"问题：{question}\n"
            f"可能原因：筛选条件过于严格或数据不存在。\n"
            f"建议：尝试调整查询条件。"
        )
    else:
        return (
            f"抱歉，系统暂时无法生成回答。\n\n"
            f"问题：{question}\n"
            f"请稍后重试。"
        )
