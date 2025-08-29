from datetime import timedelta
from pathlib import Path
from venv import logger

from minio import Minio
from minio.error import S3Error
import os
##设置全局变量
from setting import Endpoint_URL, Access_Key, Secret_Key, BUCKET_NAME


class MinioManager:
    def __init__(self, endpoint=Endpoint_URL, access_key=Access_Key, secret_key=Secret_Key, secure=False):
        # 防止传入 http://xxx:9000
        if endpoint.startswith("http://"):
            endpoint = endpoint.replace("http://", "")
            secure = False
        elif endpoint.startswith("https://"):
            endpoint = endpoint.replace("https://", "")
            secure = True
        """
        初始化Minio客户端
        :param endpoint: Minio服务的URL
        :param access_key: Minio访问密钥
        :param secret_key: Minio密钥
        :param secure: 是否使用https
        """
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def upload_file(self, file_path_or_obj, object_name=None, bucket_name=BUCKET_NAME):
        """
        上传文件到Minio
        :param bucket_name: 存储桶名称
        :param file_path_or_obj: 本地文件路径或文件对象
        :param object_name: Minio上存储的对象名称，默认是文件名
        :return: 上传结果
        """
        try:
            # 确保存储桶存在
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            # 如果输入的是文件路径
            if isinstance(file_path_or_obj, str):
                file_path = file_path_or_obj
                if object_name is None:
                    object_name = os.path.basename(file_path)
                self.client.fput_object(bucket_name, object_name, file_path)
            # 如果输入的是文件对象
            elif hasattr(file_path_or_obj, 'read'):
                file_obj = file_path_or_obj
                if object_name is None:
                    raise ValueError("If file is an object, object_name must be provided.")
                self.client.put_object(bucket_name, object_name, file_obj, file_obj.length)
            else:
                raise ValueError("Invalid file input type.")
            logger.info(f"File {object_name} uploaded successfully to {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(self,  object_name, file_path,bucket_name=BUCKET_NAME):
        """
        下载文件从Minio
        :param bucket_name: 存储桶名称
        :param object_name: Minio上存储的对象名称
        :param file_path: 本地保存的路径
        :return: 下载结果
        """
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"File {object_name} downloaded successfully to {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def delete_file(self, object_name,bucket_name=BUCKET_NAME):
        """
        删除文件
        :param bucket_name: 存储桶名称
        :param object_name: Minio上存储的对象名称
        :return: 删除结果
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"File {object_name} deleted successfully from {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False

    def upload_directory(self, directory_path, new_directory="",bucket_name=BUCKET_NAME):
        """
        上传目录下的所有文件到Minio，并保留原有的目录结构。
        :param bucket_name: 存储桶名称
        :param directory_path: 本地目录路径
        :param new_directory: MinIO中的目标目录路径
        :return: 上传结果
        """
        try:
            # 确保存储桶存在
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)

            # 遍历目录，上传文件
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    # 计算相对路径并转换为 POSIX 格式
                    object_name = Path(file_path).relative_to(Path(directory_path)).as_posix()

                    # 如果指定了新的目录路径，将其加到目标路径上
                    if new_directory:
                        object_name = Path(new_directory, object_name).as_posix()

                    # 上传文件，保持目录结构
                    self.client.fput_object(bucket_name, object_name, file_path)
                    logger.info(f"Uploaded file {file_path} as {object_name} to {bucket_name}")

            logger.info(f"All files from directory {directory_path} uploaded successfully to {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading directory: {e}")
            return False

    # 删除指定桶中的所有文件（模拟删除目录）
    def delete_directory(self, directory_name,bucket_name=BUCKET_NAME):
        try:
            # 列出桶中所有对象，过滤出目录下的对象
            objects = self.client.list_objects(bucket_name, prefix=directory_name, recursive=True)
            for obj in objects:
                # 删除每个对象
                self.client.remove_object(bucket_name, obj.object_name)
                logger.info(f"删除对象：{obj.object_name}")

            logger.info(f"目录 {directory_name} 下的所有对象已删除。")
            return True
        except S3Error as err:
            logger.error(f"删除目录发生错误: {err}")
            return False

    def modify_file(self,  object_name, new_file_path_or_obj,bucket_name=BUCKET_NAME):
        """
        修改Minio上的文件，实际上是删除旧文件然后上传新文件
        :param bucket_name: 存储桶名称
        :param object_name: Minio上存储的对象名称
        :param new_file_path_or_obj: 新文件的路径或文件对象
        :return: 修改结果
        """
        try:
            # 删除旧文件
            self.delete_file(bucket_name, object_name)
            # 上传新文件
            return self.upload_file(bucket_name, new_file_path_or_obj, object_name)
        except S3Error as e:
            logger.error(f"Error modifying file: {e}")
            return False

    def get_file_url(self,  object_name,bucket_name=BUCKET_NAME):
        url = self.client.presigned_get_object(bucket_name, object_name, expires=timedelta(hours=24))
        return url


# 示例使用
if __name__ == "__main__":
    minio_client = MinioManager(endpoint=Endpoint_URL, access_key=Access_Key,
                                secret_key=Secret_Key,secure=False)

    # 上传单个文件
    result = minio_client.upload_file(file_path_or_obj= "D:/system/photo/工资/6月.jpg", object_name='static/game/__INLINE__58.png')
    print(result)

    print(minio_client.get_file_url(BUCKET_NAME, 'static/game/__INLINE__58.png'))
    #
    # # 下载文件
    # result = minio_client.download_file('mybucket', 'file.txt', 'path/to/local/save/file.txt')
    # print(result)
    #
    # # 删除文件
    # result = minio_client.delete_file('mybucket', 'file.txt')
    # print(result)

    # # 上传目录
    # image_path = os.path.join(STATIC_ROOT, 'perfetto', '2022-11-30')
    # result = minio_client.upload_directory(bucket_name='perfetto', directory_path=image_path, new_directory='2022-11-30')
    # print(result)

    # 删除目录
    # result = minio_client.delete_directory('perfetto', '')
    # print(result)

    # # 修改文件
    # result = minio_client.modify_file('mybucket', 'file.txt', 'path/to/new/local/file.txt')
    # print(result)
