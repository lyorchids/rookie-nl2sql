"""
Generate Answer Node.
Converts SQL execution results into user-friendly natural language reports.
Uses if/else to select appropriate prompt template based on scenario.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

from langchain_core.messages import HumanMessage
from pyexpat.errors import messages

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.llm_client import llm_client, LLMClient
from tools.utils import load_prompt_template
from graphs.state import NL2SQLState

async def generate_answer_node(state: NL2SQLState) -> NL2SQLState:
    """
    Generate a natural language answer based on query results.
    Uses if/else to select the appropriate prompt template for each scenario.
    """
    question = state.get("question", "")
    candidate_sql = state.get("candidate_sql")
    execution_result = state.get("execution_result")
    sandbox = state.get("sandbox")
    intent = state.get("intent")

    print(f"\n=== Generate Answer Node ===")

    show=f"根据问题生成最终答案, 执行标准："

    # If irrelevant question, let LLM answer directly without template
    if intent and not intent.get("is_relevant", True):
        scenario = "irrelevant"
        show += "无关问题"
        try:
            messages = []
            prompt = f"请友好地回答用户的问题（注意：这不是数据库查询请求，而是普通对话）：\n{question}"

            messages.append(HumanMessage(content=prompt))
            llm = LLMClient(stream=True).client
            response = await llm.ainvoke(messages)
            full_response = response.content

            return {
                **state,
                "show": show,
                "answer": full_response
            }
        except Exception as e:
            print(f"\n✗ Error generating answer: {e}")
            return {
                **state,
                "answer": f"抱歉，我暂时无法回答这个问题。",
            }

    # Determine scenario and select template using if/else
    if sandbox and not sandbox.get("is_safe", True):
        # Scenario: Sandbox blocked
        scenario = "blocked"
        show += "不安全sql"
        prompt_template = load_prompt_template("answer_blocked")
        prompt = prompt_template.format(
            question=question,
            candidate_sql=candidate_sql or "未生成 SQL",
            error=sandbox.get("blocked_reason", "安全拦截")
        )
    elif not candidate_sql:
        # Scenario: No SQL generated
        scenario = "no_sql"
        show += "没有sql生成"
        prompt_template = load_prompt_template("answer_no_sql")
        prompt = prompt_template.format(
            question=question
        )
    elif execution_result is None:
        # Scenario: No execution result
        scenario = "no_execution"
        show += "没有执行结果"
        prompt_template = load_prompt_template("answer_error")
        prompt = prompt_template.format(
            question=question,
            candidate_sql=candidate_sql,
            error="未执行查询"
        )
    elif execution_result.get("ok"):
        if execution_result.get("row_count", 0) == 0:
            # Scenario: Success but empty result
            scenario = "empty"
            show += "查询成功但返回为行数为0"
            prompt_template = load_prompt_template("answer_empty")
            execution_result_str = _format_execution_result(execution_result, scenario)
            prompt = prompt_template.format(
                question=question,
                candidate_sql=candidate_sql,
                execution_result=execution_result_str
            )
        else:
            # Scenario: Success with data
            scenario = "success"
            show += "查询成功"
            prompt_template = load_prompt_template("answer_success")
            execution_result_str = _format_execution_result(execution_result, scenario)
            prompt = prompt_template.format(
                question=question,
                candidate_sql=candidate_sql,
                execution_result=execution_result_str
            )
    else:
        # Scenario: Execution error
        scenario = "error"
        show += "执行sql失败"
        prompt_template = load_prompt_template("answer_error")
        prompt = prompt_template.format(
            question=question,
            candidate_sql=candidate_sql,
            error=execution_result.get("error", "未知错误")
        )

    print(f"Scenario: {scenario}")

    # Call LLM to generate answer
    try:
        messages = []
        messages.append(HumanMessage(content=prompt))
        llm = LLMClient(stream=True).client
        response = await llm.ainvoke(messages)
        full_response = response.content

        return {
            **state,
            "show": show,
            "answer": full_response
        }

    except Exception as e:
        print(f"\n✗ Error generating answer: {e}")
        fallback_answer = _generate_fallback_answer(question, scenario, execution_result, sandbox)
        return {
            **state,
            "answer": fallback_answer,
        }

def _format_execution_result(execution_result, scenario):
    """Format execution result into a readable string for the prompt."""
    if not execution_result:
        return "无执行结果"

    if scenario == "empty":
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

def _generate_fallback_answer(question, scenario, execution_result, sandbox):
    """Generate a fallback answer when LLM call fails."""
    if scenario == "blocked":
        return (
            f"⚠️ 安全警告\n\n"
            f"您的查询已被安全系统拦截。\n"
            f"原因：{sandbox.get('blocked_reason', '安全拦截')}\n\n"
            f"本系统仅允许只读查询（SELECT），以确保数据安全。\n"
            f"请尝试提出其他查询需求。"
        )
    elif scenario == "no_sql":
        return (
            f"抱歉，系统未能生成有效的 SQL 查询。\n\n"
            f"问题：{question}\n"
            f"请尝试用更明确的方式重新描述您的需求。"
        )
    elif scenario == "error" or scenario == "no_execution":
        error_msg = execution_result.get("error", "未知错误") if execution_result else "未执行查询"
        return (
            f"查询执行失败。\n\n"
            f"问题：{question}\n"
            f"错误信息：{error_msg}\n\n"
            f"请尝试重新提问或联系管理员。"
        )
    elif scenario == "empty":
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
