"""
Table selection node for NL2SQL system.
M3: Enhanced schema understanding with intelligent table selection.
"""
import json
from pathlib import Path
from langchain.tools import tool
import sys
from langchain.agents import create_agent

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


from tools.db import db_client
from tools.llm_client import llm_client
from tools.utils import load_prompt_template, extract_tables_from_response, parse_table_string_to_array
from graphs.state import NL2SQLState

@tool
def get_table_schema(table_name: str) -> str:
    """
    获取指定表的详细结构信息（字段名、类型、约束等）

    Args:
        table_name: 表名

    Returns:
        JSON字符串，包含表结构信息
    """
    try:
        schema = db_client.get_table_schema(table_name)
        return json.dumps(schema, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def get_table_relationships(table_name: str) -> str:
    """
    获取指定表的外键关系信息

    Args:
        table_name: 表名

    Returns:
        JSON字符串，包含外键关系列表
    """
    try:
        schema = db_client.get_table_relationships(table_name)
        return json.dumps(schema, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool
def get_all_tables_schemas() -> str:
    """
    Get basic database schema string (fallback).

    Returns:
        Formatted basic schema string
    """
    schema_lines = []

    # Get all table names
    tables = db_client.get_table_names()

    for table_name in tables:
        # Get table schema
        table_schema = db_client.get_table_schema(table_name)
        columns = table_schema.get("columns", [])

        # Extract column names
        column_names = [col["name"] for col in columns]

        # Format string
        columns_str = ", ".join(column_names)
        schema_lines.append(f"- {table_name} ({columns_str})")
    return "\n".join(schema_lines)

def select_tables_node(state: NL2SQLState) -> NL2SQLState:
    """
    Select relevant tables based on the user question.

    Args:
        state: Current NL2SQL state

    Returns:
        Updated state with selected tables
    """
    question = state.get("question", "")

    print(f"\n=== Select Tables Node ===")

    tools = [get_table_schema, get_table_relationships, get_all_tables_schemas]

    try:
        prompt_template = load_prompt_template("table_selection_with_tools")
        prompt = prompt_template.format(question=question)

        print(f"\n=== Table Selection Prompt ===")
        print(f"Prompt length: {len(prompt)} characters")

        agent = create_agent(
            model=llm_client.client,
            system_prompt="你是一名数据库架构专家和NL2SQL助手",
            tools=tools,
        )

        response = agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        result = response['messages'][-1].content
        print(f"\nLLM Response:\n{result}")

        selected_tables_str = extract_tables_from_response(result)
        print(f"\nSelected Tables: \n{selected_tables_str}")

        valid_tables = db_client.get_table_names()
        parsed_tables = parse_table_string_to_array(selected_tables_str)
        validated_tables = [t for t in parsed_tables if t in valid_tables]
        invalid_tables = [t for t in parsed_tables if t not in valid_tables]

        if invalid_tables:
            print(f"⚠ Warning: Invalid table names filtered out: {invalid_tables}")

        if not validated_tables:
            print("⚠ Warning: No valid tables selected, falling back to all tables")
            validated_tables = valid_tables

        return {
            **state,
            "schema": selected_tables_str,
            "tables": validated_tables,
        }

    except Exception as e:
        print(f"✗ Error selecting tables: {e}")
        valid_tables = db_client.get_table_names()
        print(f"✓ Falling back to all tables: {valid_tables}")
        return {
            **state,
            "schema": "",
            "tables": valid_tables,
        }


if __name__ == '__main__':
    test_state: NL2SQLState = {
        "question": "查询每个员工的销售业绩，包括处理的发票数量、总销售额和平均每单金额",
        "session_id": f"test-1",
        "timestamp": None,
        "intent": None,
        "candidate_sql": None,
        "sql_generated_at": None,
    }
    print(select_tables_node(test_state))


