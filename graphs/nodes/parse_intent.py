"""
Parse Intent Node for NL2SQL system.
Uses LLM to analyze user questions, determine relevance, and normalize them.
"""
import json
from datetime import datetime
from pathlib import Path
import sys
# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.llm_client import llm_client
from tools.utils import load_prompt_template
from graphs.state import NL2SQLState


def parse_intent_node(state: NL2SQLState) -> NL2SQLState:
    """
    Parse user intent from the question using LLM.
    Determines if the question is database-related and normalizes it.
    """
    question = state.get("question", "")

    print(f"\n=== Parse Intent Node ===")
    print(f"Question: {question}")

    try:
        prompt_template = load_prompt_template("intent_recognition")
        prompt = prompt_template.format(question=question)

        response = llm_client.chat(prompt=prompt)
        print(f"\nLLM Response:\n{response}")

        # Extract JSON from response using multiple strategies
        json_str = None

        # Strategy 1: Extract from ```json code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                json_str = response[start:end].strip()
                print(f"\nExtracted JSON from ```json block")

        # Strategy 2: Extract from ``` code block
        if json_str is None and "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                json_str = response[start:end].strip()
                print(f"\nExtracted JSON from ``` block")

        # Strategy 3: Extract from first { to last }
        if json_str is None:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                print(f"\nExtracted JSON using brace matching")

        # Parse JSON
        if json_str:
            print(f"\nJSON String (first 300 chars):\n{json_str[:300]}")
            try:
                intent = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"\nJSON Decode Error: {e}")
                # Try to clean up common issues
                json_str_clean = json_str.strip()
                # Remove any markdown artifacts
                if json_str_clean.startswith("json"):
                    json_str_clean = json_str_clean[4:].strip()
                intent = json.loads(json_str_clean)
        else:
            print(f"\nWarning: Could not extract JSON, using fallback")
            intent = {
                "is_relevant": True,
                "intent_type": "unknown",
                "normalized_question": question,
                "entities": [],
                "time_range": None,
                "reason": "Failed to extract JSON from LLM response, defaulting to relevant"
            }

        print(f"\nParsed Intent:")
        print(f"  is_relevant: {intent.get('is_relevant')}")
        print(f"  intent_type: {intent.get('intent_type')}")
        print(f"  normalized_question: {intent.get('normalized_question')}")
        print(f"  reason: {intent.get('reason')}")

        # If question is irrelevant, set answer directly
        if not intent.get("is_relevant", True):
            irrelevant_answer = f"抱歉，您的问题'{question}'与数据库查询无关。我可以帮您查询数据库相关信息，请重新提问。"
            return {
                **state,
                "intent": intent,
                "answer": irrelevant_answer,
                "timestamp": datetime.now().isoformat()
            }

        # If relevant, normalize the question
        normalized_question = intent.get("normalized_question", question)
        return {
            **state,
            "intent": intent,
            "question": normalized_question,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"\n✗ Error parsing intent: {e}")
        # Fallback to simple parsing
        intent = {
            "is_relevant": True,
            "intent_type": "unknown",
            "normalized_question": question,
            "entities": [],
            "time_range": None,
            "reason": f"Error during LLM parsing: {str(e)}"
        }
        return {
            **state,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }


def route_after_intent(state: NL2SQLState) -> str:
    """
    Routing function to decide next step after intent parsing.
    Returns "generate_answer" if irrelevant, "select_tables" if relevant.
    """
    intent = state.get("intent", {})
    is_relevant = intent.get("is_relevant", True)

    if not is_relevant:
        print(f"\n→ Routing to generate_answer (irrelevant question)")
        return "generate_answer"
    else:
        print(f"\n→ Routing to select_tables (relevant question)")
        return "select_tables"


if __name__ == '__main__':
    test_cases = [
        {"question": "有多少名艺术家发布了专辑", "expected_relevant": True},
        {"question": "你好，今天天气怎么样", "expected_relevant": False},
        {"question": "显示所有客户的信息", "expected_relevant": True},
        {"question": "Python怎么写循环", "expected_relevant": False},
        {"question": "找出销售额最高的前10个客户", "expected_relevant": True},
    ]

    print("=" * 60)
    print("Intent Recognition Test")
    print("=" * 60)

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {case['question']}")
        print(f"{'='*60}")

        test_state: NL2SQLState = {
            "question": case["question"],
            "session_id": f"test-{i}",
            "timestamp": None,
            "intent": None,
        }

        result = parse_intent_node(test_state)
        intent = result.get("intent", {})

        is_relevant = intent.get("is_relevant")
        expected = case["expected_relevant"]
        status = "✓" if is_relevant == expected else "✗"

        print(f"\n{status} Expected relevant={expected}, Got relevant={is_relevant}")
        print(f"  Intent Type: {intent.get('intent_type')}")
        print(f"  Normalized: {intent.get('normalized_question')}")

        if not is_relevant:
            print(f"  Answer: {result.get('answer')}")
        else:
            print(f"  Question: {result.get('question')}")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print(f"{'='*60}")
