import os
import string
import uuid
from random import random

from docxtpl import DocxTemplate

from utils.minio_utils import MinioManager

def delete_file(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        print(f"已删除文件: {file_path}")
        return True
    else:
        print(f"文件不存在: {file_path}")
        return False

##生成文件并上传 获得url
def generation_sava_minio(template_name:str,context:dict):
    # 获取当前脚本目录
    current_dir = os.path.dirname(__file__)
    # 上一级目录
    parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
    # 拼接 tax_audit/template/xxx.docx
    doc_name = os.path.join(parent_dir, "tax_audit", "template", f"{template_name}.docx")

    doc = DocxTemplate(doc_name)
    doc.render(context)
    ##保存文件 命名  "_" + ''.join(random.choices(string.ascii_letters + string.digits, k=8)) +
    file_path = template_name + uuid.uuid4().hex + ".docx"

    doc.save(file_path)  # 保存文件操作

    minio_client = MinioManager()

    # 上传单个文件
    result = minio_client.upload_file(file_path_or_obj=file_path, object_name='template/accounting/'+file_path)
    try:

        if result:
            file_url = minio_client.get_file_url(object_name='template/accounting/'+file_path)

            delete_file(file_path)

            return file_url

        else:
            return None

    except:
        file_url = None
        return file_url





