"""
Sandbox Check Node.
Performs security checks on SQL before execution.
Routes to execute_sql if safe, or to echo if unsafe.
"""
from pathlib import Path
from datetime import datetime
import sys
# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.sql_sandbox import sql_sandbox
from graphs.state import NL2SQLState


def sandbox_check_node(state: NL2SQLState) -> NL2SQLState:
    """
    Check SQL security before execution.

    Args:
        state: Current graph state containing candidate_sql

    Returns:
        Updated state with sandbox check result
    """
    candidate_sql = state.get("candidate_sql")
    question = state.get("question", "")

    print(f"\n=== Sandbox Check Node ===")

    if not candidate_sql:
        print("⚠ No SQL to check, marking as unsafe")
        sandbox_result = {
            "is_safe": False,
            "risk_level": "high",
            "warnings": ["No SQL provided"],
            "blocked_reason": "No SQL generated"
        }
    else:
        # Perform sandbox check
        sandbox_result = sql_sandbox.check(candidate_sql)
        # print(f"  is_safe: {sandbox_result['is_safe']}")
        # print(f"  risk_level: {sandbox_result['risk_level']}")

        show = f"sql沙箱验证，是否安全：{sandbox_result['is_safe']}，危险等级：{sandbox_result['risk_level']}"
        if sandbox_result['warnings']:
            show += f"警告：{sandbox_result['warnings']}"
        if sandbox_result['blocked_reason']:
            show += f"拦截原因: {sandbox_result['blocked_reason']}"
    return {
        **state,
        "sandbox": {
            **sandbox_result,
            "checked_at": datetime.now().isoformat()
        },
        "show": show
    }


def route_after_sandbox(state: NL2SQLState) -> str:
    """
    Routing function to decide next step after sandbox check.

    Returns:
        "execute_sql" if SQL is safe, "generate_answer" if unsafe
    """
    sandbox = state.get("sandbox", {})
    is_safe = sandbox.get("is_safe", False)

    if is_safe:
        print(f"\n→ Routing to execute_sql (SQL is safe)")
        return "execute_sql"
    else:
        print(f"\n→ Routing to generate_answer (SQL blocked: {sandbox.get('blocked_reason', 'unknown')})")
        return "generate_answer"
