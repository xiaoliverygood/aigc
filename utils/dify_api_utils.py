import json
import requests

from setting import DIFY_BASE_URL, DIFY_API_KEY


class DifyApiUtils:
    def __init__(self, base_url: str = None, headers: dict = None):
        # 设置基础URL
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = DIFY_BASE_URL

        # 设置请求头
        secret_key = DIFY_API_KEY
        if headers is None:
            self.headers = {
                'Authorization': f'Bearer {secret_key}',
                'Content-Type': 'application/json',
            }
        else:
            self.headers = headers

        self.data = {}

    # 调用工作流
    def workflow_run(self, user_input: str = None, user: str = "abc-123"):
        # 确保URL包含 /v1/workflows/run
        # 如果 base_url 已经包含 /v1，就不重复添加
        if self.base_url.endswith('/v1'):
            workflow_url = f"{self.base_url}/workflows/run"
        elif '/v1/' in self.base_url:
            workflow_url = f"{self.base_url}/workflows/run"
        else:
            # 如果 base_url 不包含 /v1，则添加
            workflow_url = f"{self.base_url}/v1/workflows/run"

        # 构建请求体，格式与 Apifox 案例完全一致
        self.data = {
            "inputs": {
                "user_input": user_input
            },
            "response_mode": "blocking",
            "user": user
        }

        # 调试信息
        print("请求URL:", workflow_url)
        print("请求headers:", self.headers)
        print("请求body:", json.dumps(self.data, ensure_ascii=False, indent=2))

        try:
            response = requests.post(workflow_url, headers=self.headers, json=self.data)
        except Exception as e:
            print("请求异常:", str(e))
            return False

        print("返回状态码:", response.status_code)
        print("返回内容:", response.text)

        # 处理响应
        if response.status_code == 200:
            try:
                if self.data["response_mode"] == "blocking":
                    return response.json()
                else:
                    return self.response_deal_message(response_content=response.content)
            except json.JSONDecodeError as e:
                print("JSON 解析错误:", str(e))
                return False
        else:
            print(f"API 调用失败，状态码: {response.status_code}")
            if response.text:
                print(f"错误信息: {response.text}")
            return False

    # 流式响应处理（保持不变）
    def response_deal_message(self, response_content: bytes):
        res_list = response_content.decode(encoding="utf-8").split("\n\n")
        for res in res_list:
            if not res.strip():  # 跳过空行
                continue
            temp_list = res.split(":", 1)
            if len(temp_list) < 2:  # 确保有足够的部分
                continue
            if temp_list[0] == "event":
                continue
            elif temp_list[0] == "data":
                json_str = temp_list[1].strip()
                try:
                    json_obj = self.event_deal_message(json_str)
                    if json_obj['event'] == 'message':
                        pass
                    elif json_obj['event'] == 'node_finished':
                        pass
                    if json_obj["event"] == "workflow_finished":
                        return json_obj
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"处理流式响应时出错: {e}")
                    continue
        return False

    def event_deal_message(self, json_str: str):
        event_data = json.loads(json_str)
        return event_data


if __name__ == "__main__":
    # 创建 DifyApiUtils 实例
    # 基本使用
    # dify_client = DifyApiUtils()
    # result = dify_client.workflow_run(
    #     user_input="帮清远正大集团做2024年财务审计报表，资产110万",
    #     user="abc-123"  # 可选，默认为 "abc-123"
    # )
    dify_client = DifyApiUtils()

    # 测试用例 - 与 Apifox 案例一致
    user_input = "帮清远正大集团做2024年财务审计报表，资产110万"

    result = dify_client.workflow_run(user_input=user_input, user="abc-123")

    # blocking模式的响应处理
    if result and isinstance(result, dict):
        if "data" in result:
            outputs = result["data"]["outputs"]

            print(f"输出结果: {outputs}")
        else:
            print("响应格式异常:", result)
    else:
        print("工作流执行失败")