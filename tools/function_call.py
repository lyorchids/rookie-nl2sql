"""
封装多个数据库工具，供LLM通过Function Call并行调用
用于发现表结构、表关系，实现多表联结查询的辅助工具集
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from langchain.tools import tool

def get_table_names() -> str:
    """
    获取数据库中所有表名的列表

    Returns:
        JSON字符串，包含表名列表
    """
    try:
        tables = db_client.get_table_names()
        return json.dumps({"tables": tables}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

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

def get_all_tables_schemas() -> str:
    """
    获取所有表的结构信息（谨慎使用，可能返回大量数据）

    Returns:
        JSON字符串，包含所有表的结构
    """
    try:
        schemas = db_client.get_all_schemas()
        return json.dumps(schemas, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    # schema_lines = []
    #
    # # Get all table names
    # tables = db_client.get_table_names()
    #
    # for table_name in tables:
    #     # Get table schema
    #     table_schema = db_client.get_table_schema(table_name)
    #     columns = table_schema.get("columns", [])
    #
    #     # Extract column names
    #     column_names = [col["name"] for col in columns]
    #
    #     # Format string
    #     columns_str = ", ".join(column_names)
    #     schema_lines.append(f"- {table_name} ({columns_str})")
    #
    # return "\n".join(schema_lines)

def execute_read_only_sql(sql: str) -> str:
    """
    执行只读SQL查询（SELECT语句）用于验证或探索数据

    Args:
        sql: 只读SQL查询语句（必须是SELECT开头）

    Returns:
        JSON字符串，包含查询结果
    """
    try:
        # 安全检查：只允许SELECT查询
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return json.dumps({"error": "只允许执行SELECT查询"}, ensure_ascii=False)

        result = db_client.query(sql)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == '__main__':
    print(get_all_tables_schemas())


