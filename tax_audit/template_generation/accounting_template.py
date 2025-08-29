##Accounting 会计模板生成
import json

from tax_audit.template_generation.entity.cover import ServiceItem, Cover
from utils import generation_sava_minio


def generate_accounting_template(company_name, services_data_json, year, month, day, services_description):
    """
          生成会计模板

          Args:
              company_name: 公司名称
              services_data_json: 服务数据JSON列表，格式: [{"name": "xxx", "total_fee": 123}, ...]
              year: 年份
              month: 月份
              day: 日期
              services_description: 服务描述
          """
    # 1. 解析JSON数据（如果传入的是字符串）
    if isinstance(services_data_json, str):
        services_list = json.loads(services_data_json)
    else:
        # 如果已经是列表/字典格式，直接使用
        services_list = services_data_json

    # 2. 创建ServiceItem对象列表（注意：这部分应该在if-else外面）
    services_data = []
    for service_dict in services_list:
        service_item = ServiceItem(
            name=service_dict['name'],
            total_fee=service_dict['total_fee']
        )
        services_data.append(service_item)

    # 3. 创建Cover对象
    cover = Cover(
        company_name=company_name,
        services_data=services_data,
        year=year,
        month=month,
        day=day,
        services_description=services_description
    )

    result = cover.to_dict()
    url = generation_sava_minio("accounting_juli",result)

    return url





if __name__ == "__main__":
    generate_accounting_template()
