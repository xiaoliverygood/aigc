import time
import json
import uuid
import tempfile
import os
import traceback
from datetime import datetime
from pathlib import Path

from rag import TemporalRAGSystem


# 假设你的 TemporalRAGSystem 类已经位于正确的位置
# from rag.entity.temporal_rag_system import TemporalRAGSystem


def test_single_document_import(rag_system):
    """测试单个文档导入的完整流程，并增强错误调试"""
    print("🧪 开始单个文档导入测试")
    print("=" * 50)

    # 1. 创建测试文件
    test_content = """这是一个UTF-8测试文档。

    测试内容包括：
    - 中文字符：你好世界
    - 英文字符：Hello World
    - 数字：12345
    - 特殊符号：！@#￥%…&*（）
    - 标点符号：。，；：""''？

    这个文档用于测试RAG系统的导入功能是否正常工作。
    每一行都包含不同类型的字符以确保UTF-8处理正确。

    第二段内容：
    包含更多测试文本，用于验证文本分割和向量化是否正常。
    这里有一些技术术语：机器学习、自然语言处理、向量检索。
    """
    test_file_path = None
    try:
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            test_file_path = f.name
        print(f"✅ 创建测试文件: {test_file_path}")
        print(f"📄 文件内容长度: {len(test_content)} 字符")

        # 2. 测试文件读取和内容验证
        print("\n🔍 测试文件读取...")
        content = rag_system._read_file(test_file_path)  # 调用私有方法，更直接
        if content is None:
            print("❌ 文件读取失败，内容为空。")
            return False

        print(f"✅ 文件读取成功: {len(content)} 字符")
        print(f"📝 内容预览: {repr(content[:100])}...")

        try:
            content.encode('utf-8', errors='strict')
            print("✅ 内容严格UTF-8编码验证通过")
        except UnicodeError as e:
            print(f"❌ 内容严格UTF-8编码验证失败: {e}")
            print(f"⚠️ 可能因为文件读取时使用了 'ignore' 模式，导致非UTF-8字符被跳过。")
            return False

        # 3. 测试文档处理
        print("\n⚙️ 测试文档处理...")
        processed_data = rag_system.add_or_update_document(
            file_path=test_file_path,
            expiry_days=None,
            metadata={"test_case": True, "created_by": "single_test"},
            force_new_version=True
        )

        if not processed_data or not processed_data.get("doc_id"):
            print(f"❌ 文档处理失败: {processed_data.get('summary', {}).get('message', '未知错误')}")
            return False

        print(f"✅ 文档处理成功: 生成 {processed_data.get('summary', {}).get('total_chunks')} 个chunks")
        print(f"📋 文档ID: {processed_data['doc_id']}")
        print(f"🔢 版本号: {processed_data['version']}")

        # 4. 测试数据插入
        print("\n💾 测试数据插入...")
        # 注意：add_or_update_document 内部已经处理了插入，这里直接验证结果
        original_count = rag_system.collection.num_entities
        print(f"📊 当前集合记录数: {original_count}")
        # 这里需要等待Milvus的flush操作完成
        time.sleep(1)  # 增加延迟确保Milvus处理完成

        # 验证插入结果
        query_expr = f'doc_id == "{processed_data["doc_id"]}"'
        query_result = rag_system.collection.query(
            expr=query_expr,
            output_fields=["id"],
            limit=1000
        )
        inserted_count = len(query_result)

        if inserted_count == processed_data.get('summary', {}).get('total_chunks'):
            print(f"✅ 数据插入验证通过: 成功插入 {inserted_count} 条记录")
        else:
            print(
                f"❌ 数据插入验证失败: 预期 {processed_data.get('summary', {}).get('total_chunks')} 条，实际插入 {inserted_count} 条")
            return False

        # 5. 测试搜索功能
        print("\n🔍 测试向量搜索...")
        search_results = rag_system.search_with_time_filter(
            query="这个文档的目的是什么？",
            top_k=3,
            only_latest=True
        )

        if not search_results:
            print("❌ 向量搜索失败，没有返回结果")
            return False

        print(f"✅ 向量搜索成功: 找到 {len(search_results)} 个匹配结果")
        best_result = search_results[0]
        print(f"🎯 最佳匹配:")
        print(f"  相似度: {best_result.get('score', 0):.4f}")
        print(f"  文本预览: {repr(best_result.get('text', '')[:50])}...")

        # 6. 清理测试数据
        print(f"\n🧹 清理测试数据...")
        try:
            delete_expr = f'doc_id == "{processed_data["doc_id"]}"'
            rag_system._delete_by_expr(delete_expr)
            print("✅ 测试数据已删除")
        except Exception as e:
            print(f"⚠️  清理测试数据失败: {e}")

        print(f"\n🎉 单个文档测试完成！所有步骤都成功！")
        return True

    except Exception as e:
        print(f"❌ 测试过程出现异常: {e}")
        traceback.print_exc()
        return False
    finally:
        if test_file_path and os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"🗑️  已删除临时文件: {test_file_path}")

test_single_document_import(TemporalRAGSystem())