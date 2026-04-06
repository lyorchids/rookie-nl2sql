from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class testState(TypedDict):


    # 用户输入
    question: str
    # 意图解析
    intent: Optional[Dict[str, Any]]

    # 元数据
    timestamp: Optional[str]
    session_id: Optional[str]
    #用户信息
    user_id: Optional[str]
    #对话历史
    messages: Optional[List[Dict]]
    intent_confirmed: bool  # 意图是否确认

    # 最终输出
    answer: str





