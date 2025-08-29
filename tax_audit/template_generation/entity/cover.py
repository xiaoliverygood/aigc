import requests


class ServiceItem:
    """单个服务项目类"""

    def fee_to_big_fee(self,fee_number):
        """
               将数字金额转换为大写金额

               Args:
                   fee_number: 数字金额（float或int）

               Returns:
                   str: 大写金额字符串，失败时返回空字符串
               """
        try:
            # 确保金额有效
            amount = float(fee_number)
            if amount < 0:
                print(f"警告：金额不能为负数: {amount}")
                return ""

            # 调用API转换
            res = requests.post(
                "https://www.iamwawa.cn/home/renminbi/ajax",
                data={"money": f"{amount:.2f}"},
                timeout=5
            )

            res_json = res.json()
            if res_json.get("status") == 1:
                return res_json["data"]
            else:
                error_msg = res_json.get("info", "未知错误")
                print(f"大写金额转换服务返回失败：{error_msg}")
                return ""

        except requests.exceptions.Timeout:
            print("大写金额转换超时")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败：{e}")
            return ""
        except Exception as e:
            print(f"大写金额转换失败：{e}")
            return ""

    def __init__(self, name, total_fee, big_total_fee=""):
        """
        Args:
            name: 服务名称
            total_fee: 服务费用（数值类型）
            big_total_fee: 大写金额（可选，为空时自动生成）
        """
        self.name = name
        self.total_fee = f"{total_fee:,.2f}"  # 添加千分位分隔符，保留两位小数

        # 如果没有提供大写金额，自动生成
        if not big_total_fee:
            self.big_total_fee = self.fee_to_big_fee(total_fee)
        else:
            self.big_total_fee = big_total_fee


    def to_dict(self):
        return {
            'name': self.name,
            'total_fee': self.total_fee,
            'big_total_fee': self.big_total_fee
        }

    def __str__(self):
        return f"{self.name}: {self.total_fee} ({self.big_total_fee})"


class Cover:
    """改进的Cover类 - 支持多服务项目"""

    def __init__(self, company_name, services_data, year, month, day,services_description):
        """
        Args:
            company_name: 公司名称
            services_data: 服务列表格式: [ServiceItem, ...]
            year, month, day: 日期
        """
        self.company_name = company_name
        self.year = year
        self.month = month
        self.day = day
        self.services_description= services_description

        # 处理服务数据
        if not services_data:
            raise ValueError("服务数据不能为空")

        self.services = []  # 存储所有服务项目

        for service_item in services_data:
            if isinstance(service_item, ServiceItem):
                self.services.append(service_item.to_dict())
            else:
                raise ValueError("服务数据必须是ServiceItem对象")

    def to_dict(self):
        """转换为模板渲染用的字典"""
        return {
            'company_name': self.company_name,
            'services': self.services,  # 服务列表，包含每个服务的name, total_fee, big_total_fee
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'services_description':self.services_description
        }