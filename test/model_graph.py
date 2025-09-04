from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from llm.model import get_chat_model
from langgraph.graph import START, END, StateGraph, MessagesState

## 模型
llm = get_chat_model()


## 定义节点函数
def llm_process(state: MessagesState):
    user_input = state.get('messages')
    result = llm.invoke(user_input)

    # 处理不同类型的返回值
    if isinstance(result, str):
        return {"messages": [AIMessage(content=result)]}
    elif hasattr(result, 'content'):
        return {"messages": [AIMessage(content=result.content)]}
    else:
        return {"messages": [result]}  # 假设已经是AIMessage


## 创建图
work_flow = StateGraph(MessagesState)

# 添加节点
work_flow.add_node("llm", llm_process)

# 设置入口点
work_flow.set_entry_point("llm")

# 设置结束点
work_flow.add_edge("llm", END)

## 编译图
checkpointer = MemorySaver()
app = work_flow.compile(checkpointer=checkpointer)

# ✅ 正确的调用方式 - 带会话记忆
config = {"configurable": {"thread_id": "test-session-1"}}

# 第一次对话
response1 = app.invoke(
    {"messages": [HumanMessage(content="艾瑞泽8的动力怎么样")]},
    config=config
)
print("AI回复:", response1["messages"][-1].content)

# 第二次对话 - 会记住之前的对话
response2 = app.invoke(
    {"messages": [HumanMessage(content="它的油耗呢？")]},
    config=config
)
print("AI回复:", response2["messages"][-1].content)

