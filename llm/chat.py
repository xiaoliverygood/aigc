from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from llm import REDIS_URL
from llm.model import get_chat_model


# Redis 存储函数
def get_memory(session_id: str):
    return RedisChatMessageHistory(
        session_id=session_id,
        url=REDIS_URL  # 你的 Redis 地址
    )

# 创建会话
def get_conversation_chain():
    llm = get_chat_model()

    # Prompt 模板
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # 把 LLM 和 Prompt 链接起来
    chain = prompt | llm

    # 包装成带历史记录的 Runnable
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_memory,                # 获取历史记录的方法
        input_messages_key="input",  # Prompt 中用户输入的变量名
        history_messages_key="history"  # Prompt 中历史消息的变量名
    )

    return chain_with_history
