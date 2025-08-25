import os
import json
from typing import List, Dict, Any
from pathlib import Path
import hashlib

from langchain_community.embeddings import DashScopeEmbeddings
# Milvus相关
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

# 文本处理
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# 如果使用本地模型
# from sentence_transformers import SentenceTransformer
import numpy as np



from llm.model import get_embedding_model, get_chat_model


class MilvusRAGSystem:
    """Milvus向量数据库RAG系统"""

    def __init__(
            self,
            collection_name: str = "rag_documents",
            milvus_host: str = "101.126.81.112",
            milvus_port: str = "19530",
            embedding_model: DashScopeEmbeddings = get_embedding_model(),  # OpenAI模型
            dim: int = 2048,  # OpenAI embedding维度
            chunk_size: int = 500,
            chunk_overlap: int = 50
    ):
        self.collection_name = collection_name
        self.dim = dim
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 连接Milvus
        self.connect_milvus(milvus_host, milvus_port)

        # 初始化Embedding模型
        self.init_embedding_model(embedding_model)

        # 创建或加载集合
        self.collection = self.create_collection()

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

##链接向量数据库
    def connect_milvus(self, host: str, port: str):
        """连接到Milvus服务器"""
        connections.connect("default", host=host, port=port)
        print(f"成功连接到Milvus: {host}:{port}")

    def init_embedding_model(self, model_name: str):
        self.embeddings = get_embedding_model()
        # 动态算一个向量，拿到真实维度
        test_vec = self.embeddings.embed_query("test")
        self.dim = len(test_vec)

        """初始化Embedding模型"""
        print(f"Embedding模型初始化完成，维度: {self.dim}")

    def create_collection(self) -> Collection:
        """创建或获取Milvus集合"""
        # 检查集合是否存在
        if utility.has_collection(self.collection_name):
            print(f"集合 {self.collection_name} 已存在，直接加载")
            return Collection(self.collection_name)

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
        ]

        # 创建集合模式
        schema = CollectionSchema(
            fields=fields,
            description="RAG document collection"
        )

        # 创建集合
        collection = Collection(
            name=self.collection_name,
            schema=schema,
            consistency_level="Strong"
        )

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )

        print(f"成功创建集合: {self.collection_name}")
        return collection

    def read_txt_files(self, directory: str) -> List[Dict[str, str]]:
        """读取目录下的所有txt文件"""
        documents = []
        path = Path(directory)

        for txt_file in path.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        "content": content,
                        "source": str(txt_file),
                        "filename": txt_file.name
                    })
                print(f"成功读取文件: {txt_file.name}")
            except Exception as e:
                print(f"读取文件 {txt_file.name} 失败: {e}")

        return documents

    def process_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """处理文档：分块并生成向量"""
        processed_chunks = []

        for doc in documents:
            # 文本分块
            chunks = self.text_splitter.split_text(doc["content"])

            # 为每个块生成向量
            for i, chunk in enumerate(chunks):
                # 生成唯一ID
                chunk_id = hashlib.md5(
                    f"{doc['source']}_{i}_{chunk[:50]}".encode()
                ).hexdigest()

                # 生成向量
                embedding = self.embeddings.embed_query(chunk)

                processed_chunks.append({
                    "id": chunk_id,
                    "embedding": embedding,
                    "text": chunk,
                    "source": doc["source"],
                    "chunk_index": i
                })

            print(f"处理完成: {doc['filename']} - 生成 {len(chunks)} 个文本块")

        return processed_chunks

    def insert_to_milvus(self, chunks: List[Dict[str, Any]]):
        """将处理后的文本块插入Milvus"""
        if not chunks:
            print("没有数据需要插入")
            return

        # 准备数据
        ids = [chunk["id"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        sources = [chunk["source"] for chunk in chunks]
        chunk_indices = [chunk["chunk_index"] for chunk in chunks]

        # 插入数据
        data = [ids, embeddings, texts, sources, chunk_indices]
        self.collection.insert(data)

        # 刷新以确保数据持久化
        self.collection.flush()

        print(f"成功插入 {len(chunks)} 个文本块到Milvus")

    def load_documents_to_milvus(self, directory: str):
        """完整的文档加载流程"""
        print(f"开始处理目录: {directory}")

        # 1. 读取文件
        documents = self.read_txt_files(directory)
        print(f"共读取 {len(documents)} 个文件")

        # 2. 处理文档
        chunks = self.process_documents(documents)
        print(f"共生成 {len(chunks)} 个文本块")

        # 3. 插入Milvus
        self.insert_to_milvus(chunks)

        # 4. 加载集合到内存
        self.collection.load()
        print("集合已加载到内存，准备进行检索")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """向量检索"""
        # 生成查询向量
        query_embedding = self.embeddings.embed_query(query)

        # 搜索参数
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        # 执行搜索
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "chunk_index"]
        )

        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.entity.get("text"),
                    "source": hit.entity.get("source"),
                    "chunk_index": hit.entity.get("chunk_index")
                })

        return formatted_results

    def generate_answer(self, query: str, context: List[str], model: str = "gpt-3.5-turbo") -> str:
        """使用LLM生成答案"""
        # 构建提示词
        context_str = "\n\n".join(context)
        prompt = f"""基于以下上下文信息回答问题。如果上下文中没有相关信息，请说"我无法从提供的文档中找到相关信息"。

上下文信息：
{context_str}

问题：{query}

答案："""

        # 使用ChatGPT
        llm = get_chat_model()
        response = llm.predict(prompt)

        return response

    def query_rag(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """RAG查询：检索+生成"""
        # 1. 检索相关文档
        search_results = self.search(query, top_k)

        # 2. 提取上下文
        contexts = [result["text"] for result in search_results]

        # 3. 生成答案
        answer = self.generate_answer(query, contexts)

        # 4. 返回完整结果
        return {
            "query": query,
            "answer": answer,
            "sources": search_results,
            "context_used": contexts
        }

    def delete_collection(self):
        """删除集合（用于重置）"""
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            print(f"集合 {self.collection_name} 已删除")


# 使用示例
def main():
    # # 初始化RAG系统
    # rag_system = MilvusRAGSystem(
    #     collection_name="my_rag_docs",
    #     milvus_host="101.126.81.112",
    #     milvus_port="19530",
    #     # 使用OpenAI embedding
    #     embedding_model="",
    #     # 或使用本地中文模型
    #     # embedding_model="BAAI/bge-base-zh-v1.5",
    #     chunk_size=500,
    #     chunk_overlap=50
    # )
    #
    # # 加载文档
    # documents_directory = "../广东税务文件/文件内容"  # 你的txt文件目录
    # rag_system.load_documents_to_milvus(documents_directory)

    # 进行RAG查询
    # 只初始化，不再加载文件
    rag_system = MilvusRAGSystem(
        collection_name="my_rag_docs",  # 改成你存数据时用的集合名
        milvus_host="101.126.81.112",
        milvus_port="19530"
    )

    query = "市场监管总局等九部门关于推进高效办成个体工商户转型为企业“一件事”加大培育帮扶力度的指导意见"
    result = rag_system.query_rag(query, top_k=5)
    print(result)

    print(f"\n问题: {result['query']}")
    print(f"\n答案: {result['answer']}")
    print(f"\n使用的文档来源:")
    for source in result['sources']:
        print(f"  - {source['source']} (相似度: {source['score']:.4f})")



if __name__ == "__main__":
    main()