import hashlib
import chardet
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from langchain_community.embeddings import DashScopeEmbeddings
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

from langchain.text_splitter import RecursiveCharacterTextSplitter
##获取模型 从llm中
from llm.model import get_embedding_model


class TemporalRAGSystem:
    """支持时效性管理的RAG系统，所有Milvus操作已封装"""

    def __init__(
            self,
            collection_name: str = "temporal_rag_documents",
            milvus_host: str = "localhost",
            milvus_port: str = "19530",
            embedding_model: DashScopeEmbeddings = get_embedding_model(),
            dim: int = 1024,
            chunk_size: int = 500,
            chunk_overlap: int = 50
    ):

        self.dim = dim
        self.collection_name = collection_name
        self.embeddings = embedding_model

        # 动态获取维度
        test_vec = self.embeddings.embed_query("test")
        self.dim = len(test_vec)

        # 连接Milvus
        try:
            connections.connect("default", host=milvus_host, port=milvus_port)
            print("Successfully connected to Milvus.")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            raise

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

        # 创建或加载集合
        self.collection = self._create_collection()

    def _create_collection(self) -> Collection:
        """私有方法：创建或加载支持时效性的集合"""
        if utility.has_collection(self.collection_name):
            print(f"Collection '{self.collection_name}' already exists.")
            collection = Collection(self.collection_name)
            collection.load()
            return collection

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="timestamp", dtype=DataType.INT64),
            FieldSchema(name="version", dtype=DataType.INT64),
            FieldSchema(name="expiry_time", dtype=DataType.INT64),
            FieldSchema(name="is_latest", dtype=DataType.BOOL),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        schema = CollectionSchema(fields=fields, description="Temporal RAG document collection")
        collection = Collection(name=self.collection_name, schema=schema, consistency_level="Bounded")

        # 创建索引
        vector_index = {"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}}
        collection.create_index(field_name="embedding", index_params=vector_index)
        collection.create_index(field_name="doc_id")
        collection.create_index(field_name="timestamp")
        collection.create_index(field_name="is_latest")
        collection.load()
        print(f"Successfully created and loaded collection: {self.collection_name}")
        return collection

    def _insert_chunks(self, chunks_data: List[Dict[str, Any]]):
        """私有方法：批量插入chunks数据到Milvus"""
        if not chunks_data:
            return

        # 准备数据，按字段列表
        ## 添加数据【{“”：“”，“”：“”}】
        data_to_insert = [
            [d["id"] for d in chunks_data],
            [d["doc_id"] for d in chunks_data],
            [d["embedding"] for d in chunks_data],
            [d["text"] for d in chunks_data],
            [d["source"] for d in chunks_data],
            [d["chunk_index"] for d in chunks_data],
            [d["timestamp"] for d in chunks_data],
            [d["version"] for d in chunks_data],
            [d["expiry_time"] for d in chunks_data],
            [d["is_latest"] for d in chunks_data],
            [d["metadata"] for d in chunks_data]
        ]
        self.collection.insert(data_to_insert)
        self.collection.flush()
        print(f"Inserted {len(chunks_data)} chunks into Milvus.")

    def _query_milvus(self, expr: str, output_fields: List[str], limit: int = 1000) -> List[Dict[str, Any]]:
        """私有方法：封装Milvus的query操作"""
        ##TODO 了解这个方法的作用是什么
        try:
            results = self.collection.query(expr=expr, output_fields=output_fields, limit=limit)
            return results
        except Exception as e:
            print(f"Milvus query failed: {e}")
            return []

    def _delete_by_expr(self, expr: str):
        """私有方法：封装Milvus的delete操作"""
        try:
            self.collection.delete(expr)
            self.collection.flush()
            print(f"Deleted records with expression: {expr}")
        except Exception as e:
            print(f"Milvus delete failed: {e}")

    def get_latest_document_info(self, source: str) -> Dict[str, Any]:
        """获取文档最新版本信息，封装了查询逻辑"""
        safe_source = self._sanitize_string(source)
        expr = f'source == "{safe_source}" and is_latest == true'
        results = self._query_milvus(expr, ["version", "metadata"], limit=1)
        if results:
            return {
                "version": results[0].get("version", 0),
                "file_hash": results[0].get("metadata", {}).get("file_hash", "")
            }
        return {"version": 0, "file_hash": ""}

    def mark_old_versions_as_outdated(self, source: str):
        """标记旧版本为非最新，封装了查询和删除逻辑"""
        safe_source = self._sanitize_string(source)
        expr = f'source == "{safe_source}" and is_latest == true'

        # Milvus不支持in-place update，需要先删除再插入新数据，或者通过外部ID管理
        # 为了简化，这里我们只标记旧版本，后续更新会插入新数据。
        # 实际项目中，通常会先查询出旧版本ID，然后删除这些ID。
        # 考虑到你的代码逻辑，这里只保留标记功能，但它在Milvus中无法直接执行update。
        # 我将这部分逻辑移到 add_or_update_document 中，通过插入新数据并将其标记为最新来完成。
        pass

##TODO 主要的程序入口 处理或者更新文档
    def add_or_update_document(
            self,
            file_path: str,
            expiry_days: Optional[int] = None,
            metadata: Optional[Dict] = None,
            force_new_version: bool = False
    ) -> Dict[str, Any]:
        """
        统一的文档处理入口，处理文件、生成数据并插入到Milvus。
        所有Milvus的交互（版本检查、删除、插入）都在内部封装。
        """
        ##存储路径
        fixed_path = self._sanitize_string(file_path)

        # 1. 检查版本和哈希，决定是否需要更新
        file_hash = self._get_file_hash(file_path)
        ##获取最新版本 第一次的是0 获取版本号
        latest_info = self.get_latest_document_info(fixed_path)
        new_version = latest_info.get("version", 0) + 1

        if not force_new_version and file_hash == latest_info.get("file_hash"):
            return {"summary": {"message": "File content unchanged, skipping."}}

        # 2. 标记旧版本 根据是否旧版本 删除数据 （）
        if latest_info.get("version", 0) > 0:
            # 删除旧版本数据
            expr_to_delete = f'source == "{fixed_path}" and is_latest == true'
            self._delete_by_expr(expr_to_delete)

        # 3. 处理文件内容、分块、向量化
        ##TODO 核心点
        ##获取文件信息内容
        content = self._read_file(file_path)
        if not content:
            return {"summary": {"message": "File is empty or could not be read."}}

        ##文件txt文本分块
        chunks = self.text_splitter.split_text(content)
        doc_hash = hashlib.md5(Path(fixed_path).stem.encode('utf-8')).hexdigest()[:16]  # 截取16位
        doc_id = f"{doc_hash}_v{new_version}_{uuid.uuid4().hex[:8]}"

        # doc_id = f"{Path(fixed_path).stem}_v{new_version}_{uuid.uuid4().hex[:8]}"
        current_time_ms = int(time.time() * 1000)
        expiry_time_ms = current_time_ms + (expiry_days * 24 * 60 * 60 * 1000) if expiry_days else -1

        ##原始数据
        doc_metadata = self._sanitize_metadata({
            "file_hash": file_hash,
            "total_chunks": len(chunks),
            "version": new_version
        })
        if metadata:
            doc_metadata.update(self._sanitize_metadata(metadata))

        processed_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = doc_metadata.copy()
            chunk_metadata["chunk_info"] = {"index": i}
            chunk_metadata["original_name"] = Path(fixed_path).stem

            processed_chunks.append({
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "embedding": self.embeddings.embed_query(chunk_text),
                "text": chunk_text,
                "source": fixed_path,
                "chunk_index": i,
                "timestamp": current_time_ms,
                "version": new_version,
                "expiry_time": expiry_time_ms,
                "is_latest": True,
                "metadata": chunk_metadata
            })

        # 4. 插入新数据
        self._insert_chunks(processed_chunks)

        return {
            "doc_id": doc_id,
            "version": new_version,
            "summary": {
                "total_chunks": len(processed_chunks),
                "action": "updated" if latest_info.get("version", 0) > 0 else "created"
            }
        }

    def search_with_time_filter(
            self,
            query: str,
            top_k: int = 5,
            only_latest: bool = True,
            exclude_expired: bool = True,
            time_range: Optional[tuple] = None,
            specific_version: Optional[int] = None,
            sources_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        统一的搜索入口，将所有过滤条件组合后调用Milvus查询。
        """
        query_embedding = self.embeddings.embed_query(query)

        filters = []
        if only_latest:
            filters.append("is_latest == true")
        if exclude_expired:
            current_time = int(time.time() * 1000)
            filters.append(f"(expiry_time == -1 or expiry_time > {current_time})")
        if time_range:
            filters.append(f"timestamp >= {time_range[0]} and timestamp <= {time_range[1]}")
        if specific_version is not None:
            filters.append(f"version == {specific_version}")
        if sources_filter:
            source_conditions = " or ".join([f'source == "{self._sanitize_string(s)}"' for s in sources_filter])
            filters.append(f"({source_conditions})")

        expr = " and ".join(filters) if filters else None

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        output_fields = ["text", "source", "doc_id", "timestamp", "version", "expiry_time", "metadata", "chunk_index"]

        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=output_fields
        )

        formatted_results = []
        for hits in results:
            for hit in hits:
                entity = hit.entity
                result = {
                    "id": hit.id,
                    "score": hit.score,
                    "text": entity.get("text"),
                    "source": entity.get("source"),
                    "doc_id": entity.get("doc_id"),
                    "chunk_index": entity.get("chunk_index"),
                    "version": entity.get("version"),
                    "timestamp": entity.get("timestamp"),
                    "expiry_time": entity.get("expiry_time"),
                    "metadata": entity.get("metadata")
                }
                formatted_results.append(result)
        return formatted_results

    def cleanup_expired_documents(self) -> int:
        """清理过期文档，封装了查询和删除逻辑"""
        current_time = int(time.time() * 1000)
        expr = f"expiry_time != -1 and expiry_time < {current_time}"
        expired_ids = [r["id"] for r in self._query_milvus(expr, ["id"], limit=10000)]
        if expired_ids:
            delete_expr = f'id in {expired_ids}'
            self._delete_by_expr(delete_expr)
            return len(expired_ids)
        return 0

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息，封装了查询逻辑"""
        try:
            total_count = self.collection.num_entities
            latest_count = len(self._query_milvus("is_latest == true", ["id"], limit=1))
            current_time = int(time.time() * 1000)
            expired_count = len(
                self._query_milvus(f"expiry_time != -1 and expiry_time < {current_time}", ["id"], limit=1))

            return {
                "total_chunks": total_count,
                "latest_version_chunks": latest_count,
                "expired_chunks": expired_count
            }
        except Exception as e:
            print(f"Failed to get statistics: {e}")
            return {}

    # --- 辅助方法（与Milvus操作分离） ---

    def _sanitize_string(self, text: str) -> str:
        """清理字符串，确保其可以安全存入Milvus"""
        if not text: return ""
        text = str(text)
        text = text.replace('\\', '/')
        text = text.replace('"', '\\"')
        text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        return text

    def _read_file(self, file_path: str) -> Optional[str]:
        """智能读取文件内容"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
            return raw_data.decode(encoding, errors='ignore')
        except Exception as e:
            print(f"Failed to read file {file_path}: {e}")
            return None

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Failed to get hash for {file_path}: {e}")
            return ""

    def _sanitize_metadata(self, data: Any) -> Any:
        """递归清理元数据中的字符串"""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {self._sanitize_string(k): self._sanitize_metadata(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_metadata(item) for item in data]
        else:
            return data