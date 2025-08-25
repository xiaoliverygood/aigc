import os
from rag import TemporalRAGSystem
#
rag_system = TemporalRAGSystem(collection_name="guangdong_tax_documents")

document_path = "./广东税务文件/文件内容"

# 如果是文件夹，处理其中的所有文件
if os.path.isdir(document_path):
    for filename in os.listdir(document_path):
        file_path = os.path.join(document_path, filename)
        if os.path.isfile(file_path):
            try:
                print(f"处理: {filename}")
                rag_system.add_or_update_document(file_path)
                print("✅ 成功")
            except Exception as e:
                print(f"❌ {filename} 处理失败: {e}")
else:
    # 如果是单个文件，直接处理
    rag_system.process_document_with_temporal_info(document_path)

# list = rag_system.search_with_time_filter("国家")
# print(len(list))