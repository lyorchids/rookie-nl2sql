"""
Table selection node for NL2SQL system.
M3: Enhanced schema understanding with intelligent table selection.
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from langchain.tools import tool

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from tools.llm_client import llm_client
from graphs.state import NL2SQLState


def load_prompt_template(template_name: str) -> str:
    """Load prompt template from file."""
    template_path = project_root / "prompts" / f"{template_name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def get_basic_schema_string() -> str:
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

def get_table_relationships_string() -> str:
    """
    Get formatted string of table relationships.

    Returns:
        Formatted relationships string
    """
    try:
        conn = db_client.conn if hasattr(db_client, 'conn') else None
        if conn is None or not hasattr(conn, 'execute'):
            # Create a new connection if needed
            import sqlite3
            db_path = project_root / "data" / "chinook.db"
            conn = sqlite3.connect(str(db_path))

        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        relationships = []

        # Get foreign key relationships for each table
        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = cursor.fetchall()

            for fk in foreign_keys:
                # fk: (id, seq, table, from, to, on_update, on_delete, match)
                relationships.append(
                    f"• {table}.{fk[3]} → {fk[2]}.{fk[4]}"
                )

        cursor.close()
        if hasattr(db_client, 'conn') and db_client.conn is not None:
            pass  # Keep connection open if it was ours
        else:
            conn.close()

        return "\n".join(relationships) if relationships else "无外键关系"

    except Exception as e:
        print(f"Warning: Could not get table relationships: {e}")
        return "关系信息不可用"

def extract_tables_from_response(response: str) -> str:
    # 处理 ```tables ... ``` 格式
    if "```tables" in response:
        # Extract content between ```tables and ```
        start = response.find("```tables") + 9
        end = response.find("```", start)
        tables = response[start:end].strip()
    # 处理 ``` ... ``` 格式
    elif "```" in response:
        # Extract content between ``` and ```
        start = response.find("```") + 3
        end = response.find("```", start)
        tables = response[start:end].strip()
    # 处理普通文本
    else:
        # No code blocks, use the entire response
        tables = response.strip()

        # Clean up
    tables = tables.strip()

    return tables


def parse_table_string_to_array(input_string: str) -> list[str]:
    """
    解析表格字符串，提取表名数组

    Args:
        input_string: 格式如 "Invoice: InvoiceId, CustomerId, Total\nCustomer: CustomerId, FirstName, LastName"

    Returns:
        表名数组，如 ['Invoice', 'Customer', 'InvoiceLine']
    """
    if not input_string:
        return []

    tables = []

    # 按行分割
    lines = input_string.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 查找冒号位置
        if ':' in line:
            # 提取冒号前的部分作为表名
            table_name = line.split(':', 1)[0].strip()
            if table_name:
                tables.append(table_name)

    return tables

def select_tables_node(state: NL2SQLState) -> NL2SQLState:
    """
    Select relevant tables based on the user question.

    Args:
        state: Current NL2SQL state

    Returns:
        Updated state with selected tables
    """
    # Get the question
    question = state.get("question", "")

    print(f"\n=== Select Tables Node ===")
    # Check if we have cached result for this question

    selected_tables = None

    # If not cached, use LLM to select tables
    if selected_tables is None:
        try:
            # Get enhanced schema and relationships
            all_schema = get_basic_schema_string()
            relationships_placeholder = get_table_relationships_string()

            # Load prompt template
            prompt_template = load_prompt_template("table_selection")

            # Format prompt
            prompt = prompt_template.format(
                schema=all_schema.strip(),
                relationships=relationships_placeholder.strip(),
                question=question
            )

            print(f"\n=== Table Selection Prompt ===")
            print(f"Prompt length: {len(prompt)} characters")

            # Call LLM
            response = llm_client.chat(prompt=prompt)

            print(f"\nLLM Response:\n{response}")

            # Extract table list from response
            selected_tables = extract_tables_from_response(response)

            state["schema"] = selected_tables

            print(f"\nSelected Tables: \n{selected_tables}")

            #Validate table names
            valid_tables = db_client.get_table_names()
            validated_tables = []
            invalid_tables = []

            for table in parse_table_string_to_array(selected_tables):
                if table in valid_tables:
                    validated_tables.append(table)
                else:
                    invalid_tables.append(table)

            if invalid_tables:
                print(f"⚠ Warning: Invalid table names filtered out: {invalid_tables}")

            selected_tables = validated_tables

            # If no valid tables selected, fall back to all tables
            if not selected_tables:
                print("⚠ Warning: No valid tables selected, falling back to all tables")
                selected_tables = valid_tables

        except Exception as e:
            print(f"✗ Error selecting tables: {e}")
            # Fall back to all tables on error
            selected_tables = db_client.get_table_names()
            print(f"✓ Falling back to all tables: {selected_tables}")

    # Ensure we have a valid list
    if selected_tables is None:
        selected_tables = db_client.get_table_names()

    return {
        **state,
    }


def get_selected_schema_string(selected_tables: List[str]) -> str:
    """
    Get schema string for only the selected tables.

    Args:
        selected_tables: List of selected table names

    Returns:
        Formatted schema string for selected tables
    """
    schema_lines = []

    for table_name in selected_tables:
        # Get table schema
        table_schema = db_client.get_table_schema(table_name)
        columns = table_schema.get("columns", [])

        # Extract column names
        column_names = [col["name"] for col in columns]

        # Format string
        columns_str = ", ".join(column_names)
        schema_lines.append(f"- {table_name} ({columns_str})")

    return "\n".join(schema_lines)

if __name__ == '__main__':
    test_state: NL2SQLState = {
        "question": "分析每个作曲家的作品销量，找出最畅销的作曲家，并列出他们最受欢迎的3首曲目",
        "session_id": f"test-1",
        "timestamp": None,
        "intent": None,
        "candidate_sql": None,
        "sql_generated_at": None,
    }
    print(select_tables_node(test_state))


