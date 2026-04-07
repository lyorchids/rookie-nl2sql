import json
from datetime import datetime
from pathlib import Path
import sys
from tools.llm_client import llm_client
from tools.utils import load_prompt_template
from langchain_core.messages import HumanMessage

from state import testState

# nodes.py
def ask_intent_node(state: testState) -> testState:
    """询问用户意图的节点"""
    # 检查是否有历史消息（框架自动从检查点恢复）
    question = state.get("question", "")

    messages = state.get("messages", [])

    # 如果是第一次对话，没有历史
    if not messages:
        question = "您想要做什么？请告诉我您的需求。"
        return {
            "messages": messages + [{"role": "assistant", "content": question}],
            "current_question": "intent",
            "intent_confirmed": False,
            "need_more_info": False
        }

    # 有历史，说明是循环回来的，不需要重复问
    return state


def check_intent_node(state: testState) -> testState:
    """
    判断用户意图是否确认
    这个节点需要查看历史记录来理解用户是否说了"是"
    """
    messages = state.get("messages", [])

    # 获取最后一条用户消息
    last_user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "").lower()
            break

    # 判断用户是否确认
    if last_user_message and last_user_message in ["是", "是的", "对", "确认", "yes", "y"]:
        # 用户确认，进入下一个节点
        return {
            **state,
            "intent_confirmed": True,
            "messages": messages + [{"role": "assistant", "content": "好的，继续处理..."}]
        }
    else:
        # 用户没有确认或说不清楚，需要继续询问
        clarification = "请确认您的意图，如果正确请回复'是'，否则请重新描述您的需求。"
        return {
            **state,
            "intent_confirmed": False,
            "need_more_info": True,
            "messages": messages + [{"role": "assistant", "content": clarification}]
        }


def process_intent_node(state: testState) -> testState:
    """确认意图后的处理节点"""
    messages = state.get("messages", [])
    return {
        **state,
        "messages": messages + [{"role": "assistant", "content": "正在处理您的需求..."}]
    }