"""
Table selection node for NL2SQL system.
M3: Enhanced schema understanding with intelligent table selection.
"""
from pathlib import Path
from typing import List
import sys
# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from tools.llm_client import llm_client
from tools.utils import load_prompt_template, extract_tables_from_response, parse_table_string_to_array
from graphs.state import NL2SQLState

def get_basic_schema_string(tables: List[str] | None = None) -> str:
    """
    Get basic database schema string with column types and constraints.

    Args:
        tables: Optional list of table names. If None, fetches all tables from DB.

    Returns:
        Formatted schema string including field types and constraints
    """
    schema_lines = []

    if tables is None:
        tables = db_client.get_table_names()

    for table_name in tables:
        table_schema = db_client.get_table_schema(table_name)
        columns = table_schema.get("columns", [])

        column_parts = []
        for col in columns:
            parts = [col["name"], col["type"]]
            if col.get("primary_key"):
                parts.append("PK")
            if col.get("not_null"):
                parts.append("NOT NULL")
            column_parts.append(" ".join(parts))

        columns_str = ", ".join(column_parts)
        schema_lines.append(f"- {table_name} ({columns_str})")

    return "\n".join(schema_lines)

def get_table_relationships_string(tables: List[str]) -> str:
    """
    Get formatted string of table relationships.

    Args:
        tables: List of table names to check for relationships.

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

    valid_tables = []
    all_schema_str = ""
    relationships_str = ""

    try:
        valid_tables = db_client.get_table_names()
        all_schema_str = get_basic_schema_string(valid_tables)
        relationships_str = get_table_relationships_string(valid_tables)

        max_retries = 2
        retry_count = 0
        selected_tables = None
        invalid_tables = []
        previous_response = ""

        while retry_count <= max_retries:
            try:
                if retry_count == 0:
                    prompt_template = load_prompt_template("table_selection")
                    prompt = prompt_template.format(
                        schema=all_schema_str.strip(),
                        relationships=relationships_str.strip(),
                        question=question
                    )
                else:
                    retry_prompt_template = load_prompt_template("table_selection_retry")
                    invalid_tables_str = ", ".join(invalid_tables)
                    valid_tables_str = ", ".join(valid_tables)
                    prompt = retry_prompt_template.format(
                        schema=all_schema_str.strip(),
                        invalid_tables=invalid_tables_str,
                        valid_tables=valid_tables_str,
                        question=question,
                        previous_response=previous_response
                    )


                response = llm_client.chat(prompt=prompt)
                previous_response = response
                selected_tables_str = extract_tables_from_response(response)
                print(f"\nSelected Tables: \n{selected_tables_str}")

                parsed_tables = parse_table_string_to_array(selected_tables_str)
                invalid_tables = [t for t in parsed_tables if t not in valid_tables]
                validated_tables = [t for t in parsed_tables if t in valid_tables]

                if not invalid_tables and validated_tables:
                    print(f"✓ All table names are valid")
                    return {
                        **state,
                        "schema": selected_tables_str,
                        "tables": validated_tables,
                    }
                else:
                    print(f"⚠ Invalid table names: {invalid_tables}")
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"  Retrying with LLM fix (attempt {retry_count + 1}/{max_retries + 1})...")
                    else:
                        print(f"  ✗ Max retries ({max_retries}) reached")

            except Exception as e:
                print(f"✗ Error during table selection attempt {retry_count + 1}: {e}")
                retry_count += 1
                if retry_count > max_retries:
                    break

        print("⚠ No valid tables selected after retries, falling back to all tables with full schema")
        selected_tables = valid_tables
        schema_result = all_schema_str

    except Exception as e:
        print(f"✗ Error selecting tables: {e}")
        selected_tables = valid_tables
        schema_result = all_schema_str
        print(f"✓ Falling back to all tables: {selected_tables}")

    return {
        **state,
        "schema": schema_result,
        "tables": selected_tables,
    }

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