"""
SQL Validator using sqlglot for syntax validation.
Supports configurable database dialect (default: sqlite).
"""
import sqlglot
from sqlglot.errors import ParseError
from typing import Dict, List, Optional


class SQLValidator:
    """
    SQL syntax validator using sqlglot.
    Validates SQL syntax and returns structured error information.
    """

    def __init__(self, dialect: str = "sqlite"):
        """
        Initialize validator with database dialect.

        Args:
            dialect: Database dialect for sqlglot (sqlite, mysql, postgres, etc.)
        """
        self.dialect = dialect

    def validate(self, sql: str) -> Dict:
        """
        Validate SQL syntax.

        Args:
            sql: SQL statement to validate

        Returns:
            Dict with:
                - is_valid: bool
                - errors: list of error messages
                - suggestion: human-readable error description
        """
        if not sql or not sql.strip():
            return {
                "is_valid": False,
                "errors": ["SQL is empty or None"],
                "suggestion": "请生成有效的 SQL 语句"
            }

        try:
            # Parse SQL with specified dialect
            sqlglot.parse(sql, dialect=self.dialect)
            return {
                "is_valid": True,
                "errors": [],
                "suggestion": ""
            }
        except ParseError as e:
            # Extract meaningful error message
            error_msg = str(e)
            return {
                "is_valid": False,
                "errors": [error_msg],
                "suggestion": self._format_error_suggestion(error_msg, sql)
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [str(e)],
                "suggestion": f"SQL 语法错误：{str(e)}"
            }

    def _format_error_suggestion(self, error_msg: str, sql: str) -> str:
        """
        Format error message into a human-readable suggestion.

        Args:
            error_msg: Raw error message from sqlglot
            sql: Original SQL statement

        Returns:
            Formatted suggestion string
        """
        # Extract line number and context if available
        lines = error_msg.split("\n")
        context = lines[0] if lines else error_msg

        return (
            f"SQL 语法验证失败。错误信息：{context}\n"
            f"请检查 SQL 语句的语法是否正确，特别是括号、引号、关键字的使用。"
        )


# Global instance with default sqlite dialect
sql_validator = SQLValidator(dialect="sqlite")
