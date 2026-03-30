"""
Base LangGraph for NL2SQL system.
Minimal runnable implementation with input/output nodes.
"""
import sys
import os
from langgraph.graph import StateGraph, END
from datetime import datetime
import uuid
import json
import time
from functools import wraps

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    from graphs.state import NL2SQLState
    from graphs.nodes.generate_sql import generate_sql_node
    from graphs.nodes.execute_sql import execute_sql_node
    from graphs.nodes.select_tables import select_tables_node
except ImportError:
    from state import NL2SQLState
    from nodes.generate_sql import generate_sql_node
    from nodes.execute_sql import execute_sql_node
    from nodes.select_tables import select_tables_node

def parse_intent_node(state: NL2SQLState) -> NL2SQLState:
    """
    Parse user intent from the question.
    M0: Simple intent extraction with metadata.
    """
    question = state.get("question", "")
    question_lower = question.lower()

    if any(kw in question_lower for kw in ["统计", "多少", "总计", "count", "sum"]):
        question_type = "aggregation"
    elif any(kw in question_lower for kw in ["排名", "top", "前", "最"]):
        question_type = "ranking"
    elif any(kw in question_lower for kw in ["查询", "显示", "show", "select"]):
        question_type = "select"
    else:
        question_type = "unknown"

    # 2. 提取数量词
    import re
    numbers = re.findall(r'\d+', question)
    limit = int(numbers[0]) if numbers else None

    # 3. 检测时间范围
    has_time = any(kw in question_lower
                    for kw in ["今天", "本月", "本年", "yesterday", "last"])

    # Simple intent parsing - will be enhanced in future modules
    intent = {
        "type": "query",
        "question_length": len(question),
        "has_time_range": has_time,
        "has_keywords": any(kw in question.lower() for kw in ["查询", "多少", "什么", "哪些", "统计", "show", "what", "how many"]),
        "parsed_at": datetime.now().isoformat()
    }

    print(f"\n=== Enhanced Intent ===")
    print(f"Type: {question_type}")
    print(f"Limit: {limit}")
    print(f"Has Time Range: {has_time}")

    return {
        **state,
        "intent": intent,
        "timestamp": datetime.now().isoformat()
    }

def echo_node(state: NL2SQLState) -> NL2SQLState:
    """
    Echo node - prints current state for verification.
    M0: Simple output verification.
    """
    print(f"\n=== Echo Node ===")
    print(f"Session ID: {state.get('session_id')}")
    print(f"Question: {state.get('question')}")
    print(f"Intent: {json.dumps(state.get('intent', {}), indent=2, ensure_ascii=False)}")
    print(f"Timestamp: {state.get('timestamp')}")
    print(f"candidate_sql: {state.get('candidate_sql')}")
    print(f"sql_generated_at: {state.get('sql_generated_at')}")
    print(f"execution_result: {state.get('execution_result')}")
    print(f"executed_at: {state.get('executed_at')}")
    print(f"\n{'='*50}\n")
    return state

def log_node(state: NL2SQLState) -> NL2SQLState:
    """
    记录查询日志到文件
    :param state:
    :return:
    """
    import json
    from pathlib import Path

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "query_log.jsonl"

    log_entry = {
        "session_id": state.get("session_id"),
        "question": state.get("question"),
        "intent": state.get("intent"),
        "timestamp": state.get("timestamp"),
        "candidate_sql": state.get('candidate_sql'),
        "sql_generated_at": state.get("sql_generated_at"),

    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"✓ Log written to {log_file}")

    return state

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(state):
        start = time.time()
        result = func(state)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

def build_graph() -> StateGraph:
    """
    Build the base NL2SQL graph.
    M0: Minimal graph with parse_intent -> select_tables -> generate_sql -> echo
    """
    # Create graph
    workflow = StateGraph(NL2SQLState)

    # Add nodes
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("select_tables", select_tables_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    #workflow.add_node("log", log_node)
    workflow.add_node("echo", echo_node)

    # Define edges
    workflow.set_entry_point("parse_intent")
    workflow.add_edge("parse_intent", "select_tables")
    workflow.add_edge("select_tables", "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "echo")
    #workflow.add_edge("log", "echo")
    workflow.add_edge("echo", END)

    # Compile graph
    graph = workflow.compile()

    return graph

@monitor_performance
def run_query(question: str, session_id: str = None) -> NL2SQLState:
    """
    Run a single query through the graph.

    Args:
        question: Natural language question
        session_id: Optional session identifier

    Returns:
        Final state after graph execution
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Build graph
    graph = build_graph()

    # Initialize state
    initial_state: NL2SQLState = {
        "question": question,
        "session_id": session_id,
        "timestamp": None,
        "intent": None
    }

    # Run graph
    print(f"\n{'='*50}")
    print(f"Starting NL2SQL Graph (M0 - Scaffold)")
    print(f"{'='*50}")

    result = graph.invoke(initial_state)

    return result



if __name__ == "__main__":
    """
    M0 Acceptance Test:
    Input a question and verify that intent object is correctly printed.
    """
    # Test cases
    test_questions = [
        "分析美国市场各音乐类型的销售占比，找出最受欢迎的3种音乐类型",
    ]

    print("\n" + "="*70)
    print("M0 - NL2SQL Base Graph Test")
    print("="*70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n### Test Case {i} ###")
        result = run_query(question)
        print(f"\nFinal State Keys: {list(result.keys())}")
        print(f"Intent Parsed: {'✓' if result.get('intent') else '✗'}")

    print("\n" + "="*70)
    print("M0 Test Complete!")
    print("="*70)