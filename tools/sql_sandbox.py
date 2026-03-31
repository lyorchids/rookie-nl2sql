"""
SQL Sandbox Security Checker.
Performs comprehensive security checks on SQL before execution.
"""
import re
from typing import Dict, List, Optional


class SQLSandbox:
    """
    SQL sandbox security checker.
    Validates SQL for dangerous operations, injection attempts, and resource limits.
    """

    DEFAULT_BLOCKED_KEYWORDS = [
        # DDL
        "DROP", "CREATE", "ALTER", "TRUNCATE", "RENAME",
        # DML (write operations)
        "INSERT", "UPDATE", "DELETE", "REPLACE", "MERGE",
        # Transaction control
        "COMMIT", "ROLLBACK", "SAVEPOINT",
        # Access control
        "GRANT", "REVOKE",
        # SQLite specific dangerous operations
        "ATTACH", "DETACH",
        # PRAGMA (can modify database settings)
        "PRAGMA",
        # Stored procedures / extended commands
        "EXEC", "EXECUTE", "xp_", "sp_",
        # Shell commands (SQLite specific)
        ".shell", ".system", ".read", ".output",
    ]

    DEFAULT_ALLOWED_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "CROSS",
        "ON", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL",
        "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET",
        "AS", "DISTINCT", "ALL", "UNION", "INTERSECT", "EXCEPT",
        "COUNT", "SUM", "AVG", "MAX", "MIN", "CAST", "COALESCE", "CASE", "WHEN", "THEN", "ELSE", "END",
        "EXISTS", "WITH", "RECURSIVE", "OVER", "PARTITION", "ROW_NUMBER",
        "TRUE", "FALSE", "ASC", "DESC",
    ]

    def __init__(
        self,
        blocked_keywords: Optional[List[str]] = None,
        allowed_keywords: Optional[List[str]] = None,
        max_result_rows: int = 1000,
        max_query_length: int = 5000,
        max_join_count: int = 5,
        max_subquery_depth: int = 3,
    ):
        self.blocked_keywords = blocked_keywords or self.DEFAULT_BLOCKED_KEYWORDS
        self.allowed_keywords = allowed_keywords or self.DEFAULT_ALLOWED_KEYWORDS
        self.max_result_rows = max_result_rows
        self.max_query_length = max_query_length
        self.max_join_count = max_join_count
        self.max_subquery_depth = max_subquery_depth

    def check(self, sql: str) -> Dict:
        """
        Perform comprehensive security check on SQL.

        Args:
            sql: SQL statement to check

        Returns:
            Dict with:
                - is_safe: bool
                - risk_level: "low" | "medium" | "high"
                - warnings: list of warning messages
                - blocked_reason: str (if blocked)
        """
        if not sql or not sql.strip():
            return {
                "is_safe": False,
                "risk_level": "high",
                "warnings": ["SQL is empty"],
                "blocked_reason": "Empty SQL statement"
            }

        sql_stripped = sql.strip()
        warnings = []
        blocked_reason = None
        is_safe = True

        # Check 1: Read-only check (must start with SELECT or WITH)
        read_only_ok, reason = self._check_read_only(sql_stripped)
        if not read_only_ok:
            return {
                "is_safe": False,
                "risk_level": "high",
                "warnings": [reason],
                "blocked_reason": reason
            }

        # Check 2: Multi-statement injection
        injection_ok, reason = self._check_multi_statement(sql_stripped)
        if not injection_ok:
            return {
                "is_safe": False,
                "risk_level": "high",
                "warnings": [reason],
                "blocked_reason": reason
            }

        # Check 3: Blocked keywords
        blocked_ok, found_blocked = self._check_blocked_keywords(sql_stripped)
        if not blocked_ok:
            return {
                "is_safe": False,
                "risk_level": "high",
                "warnings": [f"Found blocked keywords: {', '.join(found_blocked)}"],
                "blocked_reason": f"SQL contains blocked keywords: {', '.join(found_blocked)}"
            }

        # Check 4: Query length
        length_ok, reason = self._check_query_length(sql_stripped)
        if not length_ok:
            warnings.append(reason)

        # Check 5: JOIN count
        join_ok, join_count = self._check_join_count(sql_stripped)
        if not join_ok:
            warnings.append(f"Too many JOINs ({join_count}), max allowed: {self.max_join_count}")

        # Check 6: Subquery depth
        depth_ok, depth = self._check_subquery_depth(sql_stripped)
        if not depth_ok:
            warnings.append(f"Subquery too deep ({depth}), max allowed: {self.max_subquery_depth}")

        # Check 7: LIMIT clause recommendation
        has_limit = self._has_limit_clause(sql_stripped)
        if not has_limit:
            warnings.append("Query has no LIMIT clause, consider adding one to prevent large result sets")

        # Determine risk level
        if len(warnings) >= 3:
            risk_level = "high"
        elif len(warnings) >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "is_safe": is_safe,
            "risk_level": risk_level,
            "warnings": warnings,
            "blocked_reason": blocked_reason
        }

    def _check_read_only(self, sql: str) -> tuple:
        """Check if SQL is read-only (SELECT or WITH)."""
        sql_upper = sql.upper().strip()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
            return True, ""
        return False, f"Only SELECT queries are allowed. Detected: {sql_upper.split()[0] if sql_upper.split() else 'empty'}"

    def _check_multi_statement(self, sql: str) -> tuple:
        """Check for multi-statement injection (multiple statements separated by semicolons)."""
        # Remove string literals to avoid false positives
        cleaned = re.sub(r"'[^']*'", "''", sql)
        # Count semicolons (excluding the final one)
        semicolons = cleaned.count(";")
        if semicolons > 1:
            return False, "Multi-statement injection detected (multiple SQL statements)"
        # Check for dangerous patterns after semicolon
        if ";" in cleaned:
            after_semicolon = cleaned.split(";", 1)[1].strip()
            if after_semicolon and not after_semicolon.isspace():
                return False, "Content detected after statement terminator"
        return True, ""

    def _check_blocked_keywords(self, sql: str) -> tuple:
        """Check for blocked/dangerous keywords."""
        sql_upper = sql.upper()
        found_blocked = []
        for keyword in self.blocked_keywords:
            # Use word boundary matching to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_upper):
                found_blocked.append(keyword)
        return len(found_blocked) == 0, found_blocked

    def _check_query_length(self, sql: str) -> tuple:
        """Check if query exceeds maximum length."""
        if len(sql) > self.max_query_length:
            return False, f"Query too long ({len(sql)} chars), max allowed: {self.max_query_length}"
        return True, ""

    def _check_join_count(self, sql: str) -> tuple:
        """Count JOIN clauses in SQL."""
        sql_upper = sql.upper()
        join_count = len(re.findall(r'\bJOIN\b', sql_upper))
        return join_count <= self.max_join_count, join_count

    def _check_subquery_depth(self, sql: str) -> tuple:
        """Estimate subquery depth by counting nested SELECT."""
        sql_upper = sql.upper()
        # Count SELECT keywords as a rough estimate of nesting depth
        select_count = len(re.findall(r'\bSELECT\b', sql_upper))
        depth = select_count  # Each nested SELECT adds one level
        return depth <= self.max_subquery_depth, depth

    def _has_limit_clause(self, sql: str) -> bool:
        """Check if SQL has a LIMIT clause."""
        sql_upper = sql.upper()
        return bool(re.search(r'\bLIMIT\b', sql_upper))


# Global instance with default settings
sql_sandbox = SQLSandbox()
