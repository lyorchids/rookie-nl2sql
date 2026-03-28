"""
State definition for NL2SQL LangGraph system.
"""
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class NL2SQLState(TypedDict):
    """
    Base state for the NL2SQL graph.

    This state will be extended in future modules with:
    - normalized_question (M7)
    - schema (M3)
    - rag_evidence (M6)
    - candidate_sql (M1)
    - validation (M4)
    - execution (M2)
    - answer (M9)
    - trace (M11)
    """
    # 用户输入
    question: str

    # 元数据
    timestamp: Optional[str]
    session_id: Optional[str]

    # 意图解析
    intent: Optional[Dict[str, Any]]

    #用户信息
    user_id: Optional[str]

    #对话历史
    dialog_history: Optional[List[Dict]]

    #候选
    candidate_sql: Optional[str]

    #SQL执行结果
    execution_result: Optional[Dict]