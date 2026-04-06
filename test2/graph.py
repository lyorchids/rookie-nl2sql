# graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from state import testState
from parse_intent import ask_intent_node, check_intent_node, process_intent_node
import uuid
# 构建图
builder = StateGraph(testState)

# 添加节点
builder.add_node("ask_intent", ask_intent_node)
builder.add_node("check_intent", check_intent_node)
builder.add_node("process_intent", process_intent_node)

# 添加边
builder.set_entry_point("ask_intent")
builder.add_edge("ask_intent", "check_intent")
builder.add_edge("check_intent", END)

# 条件边：根据意图确认状态决定下一步
def route_after_check(state: testState) -> str:
    if state.get("intent_confirmed", False):
        return "process_intent"  # 确认了，进入处理
    else:
        return "ask_intent"  # 未确认，返回重新询问

builder.add_conditional_edges(
    "check_intent",
    route_after_check,
    {
        "process_intent": "process_intent",
        "ask_intent": "ask_intent"
    }
)

builder.add_edge("process_intent", END)

# 编译图（注入检查点）
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("简化版意图确认系统（输入 'q' 退出）")
    print("-" * 40)

    # 初始状态
    current_state: testState = {
        "question": None,
        "session_id": thread_id,
        "timestamp": None,
        "intent": None,
        "messages": [],
        "intent_confirmed": False
    }

    while True:
        # 获取用户输入
        user_input = input("您: ").strip()

        # 退出检查
        if user_input.lower() == 'q':
            print("再见！")
            break

        # 获取助手响应
        result = graph.invoke(current_state, config)

        # 显示助手消息
        if result.get("messages"):
            print(f"\n助手: {result['messages'][-1]['content']}")



