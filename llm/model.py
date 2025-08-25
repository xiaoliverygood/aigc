from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from llm import DASHSCOPE_API_KEY


def get_chat_model(model_name="qwen-turbo", top_p:float=0.9, temperature=0.7):
    model = ChatTongyi(
        model=model_name,
        ##https://help.aliyun.com/zh/model-studio/models 模型列表
        api_key=DASHSCOPE_API_KEY,
        top_p=top_p,
        temperature=temperature
    )
    return model

def get_embedding_model(model_name="text-embedding-v3"):
    embeddings = DashScopeEmbeddings(
        model=model_name,
        dashscope_api_key=DASHSCOPE_API_KEY
    )

    return embeddings

