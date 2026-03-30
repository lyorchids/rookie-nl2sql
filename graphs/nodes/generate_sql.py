import sys
import os
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from graphs.state import NL2SQLState
from tools.llm_client import llm_client

def load_prompt_template(template_name: str) -> str:
    #1.获取提示词模板路径
    template_path = project_root / "prompts" / f"{template_name}.txt"
    #2.判断路径是否存在
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
    #3.读取文件并返回提示词
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_sql_from_response(response: str) -> str:
    # 处理 ```sql ... ``` 格式
    if "```sql" in response:
        # Extract content between ```sql and ```
        start = response.find("```sql") + 6
        end = response.find("```", start)
        sql = response[start:end].strip()
    # 处理 ``` ... ``` 格式
    elif "```" in response:
        # Extract content between ``` and ```
        start = response.find("```") + 3
        end = response.find("```", start)
        sql = response[start:end].strip()
    # 处理普通文本
    else:
        # No code blocks, use the entire response
        sql = response.strip()

        # Clean up
    sql = sql.strip()

    # Ensure SQL ends with semicolon
    if not sql.endswith(";"):
        sql += ";"

    return sql


def get_database_schema_string() -> str:
    """
    获取数据库中所有表名和表对应的字段字符串

    返回格式：
    - 表名1 (字段1, 字段2, ...)
    - 表名2 (字段1, 字段2, ...)

    Returns:
        str: 格式化的表结构字符串
    """
    schema_lines = []

    # 获取所有表名
    tables = db_client.get_table_names()

    for table_name in tables:
        # 获取表结构
        table_schema = db_client.get_table_schema(table_name)
        columns = table_schema.get("columns", [])

        # 提取字段名
        column_names = [col["name"] for col in columns]

        # 格式化字符串
        columns_str = ", ".join(column_names)
        schema_lines.append(f"- {table_name} ({columns_str})")

    return "\n".join(schema_lines)


def generate_sql_node(state: NL2SQLState) -> NL2SQLState:
    #1.得到问题
    question = state.get("question","")

    print(f"\n=== Execute SQL Node ===")

    print(f"\n=== Generate SQL Node ===")
    print(f"Question: {question}")

    #2.得到提示词模板
    prompt_template = load_prompt_template("nl2sqlme")

    schema_placeholder = get_database_schema_string()

    # schema_placeholder = """
    #    示例表结构 :
    #    - customers (customer_id, customer_name, city, country)
    #    - orders (order_id, customer_id, amount, order_date)
    #    - products (product_id, product_name, price, category)
    #    """

    prompt = prompt_template.format(
        schema=schema_placeholder.strip(),
        question=question
    )

    #调用大模型得到答案
    try:
        # Call LLM
        response = llm_client.chat(prompt=prompt)

        print(f"\nLLM Response:\n{response}")

        # Extract SQL from response
        candidate_sql = extract_sql_from_response(response)

        print(f"\nExtracted SQL:\n{candidate_sql}")

        return {
            **state,
            "candidate_sql": candidate_sql,
            "sql_generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"\n✗ Error generating SQL: {e}")

        return {
            **state,
            "candidate_sql": None,
            "sql_generated_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    """Test SQL generation node"""
    import sys

    print("=== SQL Generation Node Test ===\n")

    # Test cases
    test_questions = [
        "查询所有客户",
        "统计每个城市的客户数量",
        "查询销售额最高的前10个客户"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}")
        print(f"{'='*60}")

        test_state: NL2SQLState = {
            "question": question,
            "session_id": f"test-{i}",
            "timestamp": None,
            "intent": None,
            "candidate_sql": None,
            "sql_generated_at": None,
        }

        result = generate_sql_node(test_state)

        print(f"\n✓ SQL Generated:")
        print(f"  {result.get('candidate_sql')}")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}")

