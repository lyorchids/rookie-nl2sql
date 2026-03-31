"""
SQL Validation Node.
Validates SQL syntax using sqlglot and retries with LLM if validation fails.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from tools.sql_validator import sql_validator
from tools.llm_client import llm_client
from graphs.state import NL2SQLState
from graphs.nodes.generate_sql import extract_sql_from_response, load_prompt_template


def validate_sql_node(state: NL2SQLState) -> NL2SQLState:
    """
    Validate SQL syntax and retry with LLM if validation fails.

    Args:
        state: Current graph state containing candidate_sql, question, schema

    Returns:
        Updated state with validation result and potentially corrected SQL
    """
    question = state.get("question", "")
    candidate_sql = state.get("candidate_sql")
    schema = state.get("schema", "")

    print(f"\n=== Validate SQL Node ===")
    print(f"Question: {question}")
    print(f"SQL to validate: {candidate_sql}")

    # If no SQL was generated, skip validation
    if not candidate_sql:
        print("⚠ No SQL to validate, skipping validation")
        return {
            **state,
            "validation": {
                "is_valid": False,
                "errors": ["No SQL generated"],
                "retry_count": 0,
                "validated_at": datetime.now().isoformat()
            }
        }

    # Maximum retry attempts
    max_retries = 2
    retry_count = 0
    validation_result = None
    current_sql = candidate_sql

    while retry_count <= max_retries:
        # Validate SQL syntax
        validation_result = sql_validator.validate(current_sql)
        print(f"\nValidation attempt {retry_count + 1}:")
        print(f"  is_valid: {validation_result['is_valid']}")

        if validation_result["is_valid"]:
            print(f"  ✓ SQL syntax is valid!")
            break

        # Validation failed
        print(f"  ✗ SQL syntax error: {validation_result['errors'][0][:100]}...")

        if retry_count < max_retries:
            # Retry: ask LLM to fix the SQL
            print(f"\n  Retrying with LLM fix (attempt {retry_count + 2}/{max_retries + 1})...")
            current_sql = _retry_with_llm(
                question=question,
                schema=schema,
                invalid_sql=current_sql,
                error_message=validation_result["suggestion"]
            )
            retry_count += 1
        else:
            # Max retries reached
            print(f"\n  ✗ Max retries ({max_retries}) reached, using last generated SQL")
            retry_count += 1

    return {
        **state,
        "candidate_sql": current_sql,
        "validation": {
            "is_valid": validation_result["is_valid"],
            "errors": validation_result["errors"],
            "retry_count": retry_count,
            "validated_at": datetime.now().isoformat()
        }
    }


def _retry_with_llm(
    question: str,
    schema: str,
    invalid_sql: str,
    error_message: str
) -> str:
    """
    Call LLM to fix SQL based on validation error.

    Args:
        question: Original user question
        schema: Database schema string
        invalid_sql: The SQL that failed validation
        error_message: Error message from validator

    Returns:
        Fixed SQL string
    """
    try:
        # Load the SQL fix prompt template
        prompt_template = load_prompt_template("sql_fix")

        # Format prompt with context
        prompt = prompt_template.format(
            schema=schema.strip(),
            question=question,
            invalid_sql=invalid_sql,
            error_message=error_message
        )

        # Call LLM
        response = llm_client.chat(prompt=prompt)
        print(f"\n  LLM fix response:\n{response}")

        # Extract SQL from response
        fixed_sql = extract_sql_from_response(response)
        print(f"\n  Extracted fixed SQL:\n{fixed_sql}")

        return fixed_sql

    except Exception as e:
        print(f"\n  ✗ Error during LLM retry: {e}")
        # Return original SQL if LLM retry fails
        return invalid_sql
