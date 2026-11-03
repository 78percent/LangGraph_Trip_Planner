"""One model factory shared by the chat agent and structured trip planner."""

from langchain_deepseek import ChatDeepSeek
from ..config import Settings

# 聊天 Agent 和旅行规划 Agent 都使用这一个地方创建模型
def get_llm(settings: Settings) -> ChatDeepSeek:   # LangChain中的ChatDeepSeek用法, 用get_llm方法创建ai实例, 之后会多次用到
    return ChatDeepSeek(                           # 此处还将config.py中的Settings类导入，
        model=settings.llm_model_id,
        api_key=settings.llm_api_key,
        api_base=settings.llm_base_url,
        timeout=settings.llm_timeout,
        max_retries=1,                             # 当 ChatDeepSeek 对象向 DeepSeek API 发送请求时，如果遇到瞬时错误，它就会自动重试; 不重试工具调用和api错误等业务逻辑错误
        max_tokens=16000,
        # Explicitly keep the first implementation non-thinking. Tool message handling
        # is easier to inspect; switching modes requires separate integration testing.
        extra_body={'thinking': {'type': 'disabled'}},
    )
