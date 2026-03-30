import sys
import os
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, Any


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

#引用其他文件
from graphs.state import NL2SQLState
from tools.llm_client import llm_client
from tools.db import db_client

def execute_sql_node(state: NL2SQLState) -> NL2SQLState:
    print(f"\n=== Execute SQL Node ===")
    
    # 1. 获取生成的 SQL
    sql = state.get("candidate_sql")
    print(f"SQL to execute: {sql}")
    
    if not sql or not sql.strip():
        print("✗ No SQL to execute")
        return {
            **state,
            "execution_result":  {
                "ok": False,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "error": "No SQL query provided"
            },
            "executed_at": datetime.now().isoformat()
        }
    
    # 2. 调用数据库客户端执行
    try:
        result = db_client.query(sql)
        print(f"Query result: {result}")
        
        if result["ok"]:
            print(f"✓ Query successful - {result['row_count']} rows returned")
        else:
            print(f"✗ Query failed: {result['error']}")
        
        # 3. 返回更新后的 State
        return {
            **state,
            "execution_result": result,
            "executed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"✗ Unexpected error during execution: {e}")
        return {
            **state,
            "execution_result": {
                "ok": False,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "error": f"Execution error: {str(e)}"
            },
            "executed_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    """Test SQL execution node"""
    import sys

    print("=== SQL Execution Node Test ===\n")

    # Test cases
    test_cases = [
        {
            "name": "Simple SELECT",
            "sql": "SELECT * FROM Album LIMIT 5"
        },
        {
            "name": "Aggregation",
            "sql": "SELECT COUNT(*) as total FROM Album"
        },
        {
            "name": "JOIN query",
            "sql": """
                SELECT a.Title, ar.Name as Artist
                FROM Album a
                JOIN Artist ar ON a.ArtistId = ar.ArtistId
                LIMIT 5
            """
        },
        {
            "name": "Invalid SQL",
            "sql": "SELECT * FROM NonExistentTable"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test['name']}")
        print(f"{'='*60}")

        test_state: NL2SQLState = {
            "question": f"Test {i}",
            "session_id": f"test-{i}",
            "timestamp": None,
            "intent": None,
            "candidate_sql": test['sql'],
            "sql_generated_at": datetime.now().isoformat(),
            "execution_result": None,
            "executed_at": None
        }

        result = execute_sql_node(test_state)

        exec_result = result.get('execution_result', {})
        if exec_result.get('ok'):
            print(f"\n✓ Test passed")
        else:
            print(f"\n✗ Test failed (expected for invalid SQL test)")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}")