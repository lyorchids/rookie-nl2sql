"""
Common utility functions for NL2SQL nodes.
"""
from pathlib import Path

project_root = Path(__file__).parent.parent


def load_prompt_template(template_name: str) -> str:
    """Load prompt template from file."""
    template_path = project_root / "prompts" / f"{template_name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_tables_from_response(response: str) -> str:
    """Extract table selection content from LLM response."""
    if "```tables" in response:
        start = response.find("```tables") + 9
        end = response.find("```", start)
        tables = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        tables = response[start:end].strip()
    else:
        tables = response.strip()

    tables = tables.strip()
    return tables


def extract_sql_from_response(response: str) -> str:
    """Extract SQL from LLM response."""
    if "```sql" in response:
        start = response.find("```sql") + 6
        end = response.find("```", start)
        sql = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        sql = response[start:end].strip()
    else:
        sql = response.strip()

    sql = sql.strip()

    if not sql.endswith(";"):
        sql += ";"

    return sql


def parse_table_string_to_array(input_string: str) -> list[str]:
    """
    Parse table string and extract table name array.

    Args:
        input_string: Format like "Invoice: InvoiceId, CustomerId, Total\nCustomer: CustomerId, FirstName, LastName"

    Returns:
        Table name array, like ['Invoice', 'Customer', 'InvoiceLine']
    """
    if not input_string:
        return []

    tables = []
    lines = input_string.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if ':' in line:
            table_name = line.split(':', 1)[0].strip()
            if table_name:
                tables.append(table_name)

    return tables
