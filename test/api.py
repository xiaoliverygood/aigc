# 测试请求
import requests

test_data = {
    "company_name": "测试公司",
    "services": [
        {"name": "服务A", "total_fee": 100034},
        {"name": "服务B", "total_fee": 200001}
    ],
    "year": 2025,
    "month": 12,
    "day": 10,
    "services_description": "测试描述"
}

response = requests.post(
    'http://localhost:5000/api/generate_template/accounting',
    json=test_data
)
print(response.json())