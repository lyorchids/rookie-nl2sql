from pathlib import Path
from datetime import datetime
import sys
# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.db import db_client
from graphs.state import NL2SQLState
from tools.llm_client import llm_client
from tools.utils import load_prompt_template, extract_sql_from_response


def generate_sql_node(state: NL2SQLState) -> NL2SQLState:
    #1.得到问题
    question = state.get("question","")

    print(f"\n=== Generate SQL Node ===")
    #print(f"Question: {question}")

    #2.得到提示词模板
    prompt_template = load_prompt_template("nl2sqlme")

    #schema_placeholder = get_database_schema_string()
    schema = state["schema"]
    # schema_placeholder = """
    #    示例表结构 :
    #    - customers (customer_id, customer_name, city, country)
    #    - orders (order_id, customer_id, amount, order_date)
    #    - products (product_id, product_name, price, category)
    #    """

    prompt = prompt_template.format(
        schema=schema.strip(),
        question=question
    )

    #调用大模型得到答案
    try:
        # Call LLM
        response = llm_client.chat(prompt=prompt)

        #print(f"\nLLM Response:\n{response}")

        # Extract SQL from response
        candidate_sql = extract_sql_from_response(response)

        #print(f"\nExtracted SQL:\n{candidate_sql}")

        show = f"生成sql，根据提取的schema生成候选sql：\n{candidate_sql}"

        return {
            **state,
            "candidate_sql": candidate_sql,
            "show": show,
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