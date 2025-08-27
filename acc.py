import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def round_to_2_decimal(value):
    """精确到小数点2位的四舍五入"""
    decimal_value = Decimal(str(value))
    return float(decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate_financial_audit_fee(amount):
    """
    计算财务报表审计收费（分段累进计费）
    根据Excel表格：
    - 50万元以下：2,000元（固定）
    - 50-100万元部分：0.200%
    - 100-500万元部分：0.090%
    - 500-1000万元部分：0.070%
    - 1000-5000万元部分：0.050%
    - 5000万元-1亿元部分：0.030%
    - 1-5亿元部分：0.015%
    - 5-10亿元部分：0.010%
    - 10亿元以上部分：0.008%
    """
    fee = 0

    # 分段计算
    if amount <= 500000:
        fee = 2000
    elif amount <= 1000000:
        fee = 2000 + (amount - 500000) * 0.002
    elif amount <= 5000000:
        fee = 2000 + 500000 * 0.002 + (amount - 1000000) * 0.0009
    elif amount <= 10000000:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + (amount - 5000000) * 0.0007
    elif amount <= 50000000:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + 5000000 * 0.0007 + (amount - 10000000) * 0.0005
    elif amount <= 100000000:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + 5000000 * 0.0007 + 40000000 * 0.0005 + (
                    amount - 50000000) * 0.0003
    elif amount <= 500000000:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + 5000000 * 0.0007 + 40000000 * 0.0005 + 50000000 * 0.0003 + (
                    amount - 100000000) * 0.00015
    elif amount <= 1000000000:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + 5000000 * 0.0007 + 40000000 * 0.0005 + 50000000 * 0.0003 + 400000000 * 0.00015 + (
                    amount - 500000000) * 0.0001
    else:
        fee = 2000 + 500000 * 0.002 + 4000000 * 0.0009 + 5000000 * 0.0007 + 40000000 * 0.0005 + 50000000 * 0.0003 + 400000000 * 0.00015 + 500000000 * 0.0001 + (
                    amount - 1000000000) * 0.00008

    return round_to_2_decimal(fee)


def calculate_capital_verification_fee(amount, verification_type="货币"):
    """
    计算资本验证收费（分段累进计费）
    货币出资：
    - 50万元以下：1,200元（固定）
    - 50-100万元部分：0.150%
    - 100-500万元部分：0.040%
    - 500-1000万元部分：0.030%
    - 1000-5000万元部分：0.020%
    - 5000万元-1亿元部分：0.015%
    - 1-5亿元部分：0.010%
    - 5-10亿元部分：0.008%
    - 10亿元以上部分：0.006%

    其他出资：按货币出资方式收费标准的120%计收
    """
    fee = 0

    # 货币出资的基础计算
    if amount <= 500000:
        fee = 1200
    elif amount <= 1000000:
        fee = 1200 + (amount - 500000) * 0.0015
    elif amount <= 5000000:
        fee = 1200 + 500000 * 0.0015 + (amount - 1000000) * 0.0004
    elif amount <= 10000000:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + (amount - 5000000) * 0.0003
    elif amount <= 50000000:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + 5000000 * 0.0003 + (amount - 10000000) * 0.0002
    elif amount <= 100000000:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + 5000000 * 0.0003 + 40000000 * 0.0002 + (
                    amount - 50000000) * 0.00015
    elif amount <= 500000000:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + 5000000 * 0.0003 + 40000000 * 0.0002 + 50000000 * 0.00015 + (
                    amount - 100000000) * 0.0001
    elif amount <= 1000000000:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + 5000000 * 0.0003 + 40000000 * 0.0002 + 50000000 * 0.00015 + 400000000 * 0.0001 + (
                    amount - 500000000) * 0.00008
    else:
        fee = 1200 + 500000 * 0.0015 + 4000000 * 0.0004 + 5000000 * 0.0003 + 40000000 * 0.0002 + 50000000 * 0.00015 + 400000000 * 0.0001 + 500000000 * 0.00008 + (
                    amount - 1000000000) * 0.00006

    # 其他出资按120%计算
    if verification_type == "其他":
        fee = fee * 1.2

    return round_to_2_decimal(fee)


def calculate_medical_institution_audit_fee(amount):
    """
    计算医疗卫生机构等非盈利组织财务报表审计收费
    医疗卫生等机构收费标准（按财务报表审计下浮10%）：
    - 50万元以下：1,800元（固定）
    - 50-100万元部分：0.180%
    - 100-500万元部分：0.081%
    - 500-1000万元部分：0.063%
    - 1000-5000万元部分：0.045%
    - 5000万元-1亿元部分：0.027%
    - 1-5亿元部分：0.012%（1亿-5亿下浮20%）
    - 5-10亿元部分：0.007%（5亿以上下浮30%）
    - 10亿元以上部分：0.0056%
    """
    fee = 0

    if amount <= 500000:
        fee = 1800
    elif amount <= 1000000:
        fee = 1800 + (amount - 500000) * 0.0018
    elif amount <= 5000000:
        fee = 1800 + 500000 * 0.0018 + (amount - 1000000) * 0.00081
    elif amount <= 10000000:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + (amount - 5000000) * 0.00063
    elif amount <= 50000000:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + 5000000 * 0.00063 + (amount - 10000000) * 0.00045
    elif amount <= 100000000:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + 5000000 * 0.00063 + 40000000 * 0.00045 + (
                    amount - 50000000) * 0.00027
    elif amount <= 500000000:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + 5000000 * 0.00063 + 40000000 * 0.00045 + 50000000 * 0.00027 + (
                    amount - 100000000) * 0.00012
    elif amount <= 1000000000:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + 5000000 * 0.00063 + 40000000 * 0.00045 + 50000000 * 0.00027 + 400000000 * 0.00012 + (
                    amount - 500000000) * 0.00007
    else:
        fee = 1800 + 500000 * 0.0018 + 4000000 * 0.00081 + 5000000 * 0.00063 + 40000000 * 0.00045 + 50000000 * 0.00027 + 400000000 * 0.00012 + 500000000 * 0.00007 + (
                    amount - 1000000000) * 0.000056

    return round_to_2_decimal(fee)


def calculate_time_based_fee(hours_by_level):
    """
    计算计时收费
    初级助理：300元/小时
    助理：600元/小时
    注册会计师：1000元/小时
    项目经理：1500元/小时
    部门经理：2000元/小时
    合伙人（主任）会计师：3000元/小时
    """
    rates = {
        "初级助理": 300,
        "助理": 600,
        "注册会计师": 1000,
        "项目经理": 1500,
        "部门经理": 2000,
        "合伙人": 3000,
        "主任会计师": 3000
    }

    total_fee = 0
    for level, hours in hours_by_level.items():
        if level in rates:
            total_fee += rates[level] * hours

    return round_to_2_decimal(total_fee)


def calculate_audit_fee(service_item, amount, **kwargs):
    """
    根据服务项目计算审计收费
    service_item: 服务项目名称
    amount: 计费基数（资产总额或销售收入或实收资本等）
    kwargs: 额外参数（如验资类型、年数、小时数等）
    """

    # 财务报表审计
    if service_item in ["财务报表审计", "投资移民审计"]:
        return calculate_financial_audit_fee(amount)

    # 资本验证
    elif service_item == "资本验证":
        verification_type = kwargs.get("verification_type", "货币")
        return calculate_capital_verification_fee(amount, verification_type)

    # 合并、分立、清算审计（按财务报表审计的150%）
    elif service_item in ["合并、分立、清算审计", "合并分立清算审计"]:
        base_fee = calculate_financial_audit_fee(amount)
        years = kwargs.get("years", 1)

        # 如果提供了年数信息
        if years > 1:
            total_fee = 0
            for year in range(years):
                if year < 3:  # 前三年按150%
                    total_fee += base_fee * 1.5
                else:  # 超过三年按120%
                    total_fee += base_fee * 1.2
            return round_to_2_decimal(total_fee)
        else:
            return round_to_2_decimal(base_fee * 1.5)

    # 经济责任审计（按财务报表审计的150%）
    elif service_item == "经济责任审计":
        base_fee = calculate_financial_audit_fee(amount)
        years = kwargs.get("years", 1)

        if years > 1:
            total_fee = 0
            for year in range(years):
                if year < 3:  # 前三年按150%
                    total_fee += base_fee * 1.5
                else:  # 超过三年按120%
                    total_fee += base_fee * 1.2
            return round_to_2_decimal(total_fee)
        else:
            return round_to_2_decimal(base_fee * 1.5)

    # 清产核资（按财务报表审计的200%）
    elif service_item == "清产核资":
        base_fee = calculate_financial_audit_fee(amount)
        return round_to_2_decimal(base_fee * 2)

    # 外汇收支审核（计时收费，最低1000元）
    elif service_item == "外汇收支审核":
        hours_by_level = kwargs.get("hours_by_level", {})
        if hours_by_level:
            fee = calculate_time_based_fee(hours_by_level)
            return max(1000, fee)
        else:
            # 如果没有提供计时信息，返回最低收费
            return 1000

    # 特殊目的审计
    elif service_item == "特殊目的审计":
        # 可以参照经济责任审计或清产核资标准，这里默认按财务报表审计的150%
        base_fee = calculate_financial_audit_fee(amount)
        return round_to_2_decimal(base_fee * 1.5)

    # 医疗卫生机构等非盈利组织审计
    elif service_item in ["医疗卫生机构审计", "非盈利组织审计", "医疗卫生机构财务报表审计"]:
        return calculate_medical_institution_audit_fee(amount)

    # 默认按财务报表审计收费
    else:
        return calculate_financial_audit_fee(amount)


def main(company_name="待定客户", service_category="audit", service_item="财务报表审计",
         amount=0, amount_type="asset", special_requirements="", **kwargs) -> dict:
    """
    主函数：计算审计服务收费

    参数：
    - company_name: 客户名称
    - service_category: 服务类别
    - service_item: 服务项目名称
    - amount: 计费金额基数
    - amount_type: 金额类型（asset:资产总额, revenue:销售收入, capital:实收资本）
    - special_requirements: 特殊要求
    - kwargs: 其他参数（如验资类型、年数、计时信息等）

    返回：
    包含收费信息的字典
    """

    # 确保金额为数字
    try:
        amount_value = float(amount)
    except (ValueError, TypeError):
        amount_value = 0

    # 计算收费
    fee_value = calculate_audit_fee(service_item, amount_value, **kwargs)

    # 格式化金额和费用
    amount_str = str(int(amount_value)) if amount_value == int(amount_value) else f"{amount_value:.2f}"
    fee_str = str(int(fee_value)) if fee_value == int(fee_value) else f"{fee_value:.2f}"

    # 构建返回结果
    result = {
        "company_name": str(company_name),
        "service_category": str(service_category),
        "service_item": str(service_item),
        "amount": amount_str,
        "amount_type": str(amount_type),
        "special_requirements": str(special_requirements),
        "fee": fee_str,
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "calculation_details": f"根据广东省会计师事务所审计服务收费标准计算"
    }

    # 添加额外参数到结果中（如有）
    if kwargs.get("verification_type"):
        result["verification_type"] = kwargs["verification_type"]
    if kwargs.get("years"):
        result["years"] = str(kwargs["years"])
    if kwargs.get("hours_by_level"):
        result["hours_breakdown"] = kwargs["hours_by_level"]

    return result


# 测试函数
if __name__ == "__main__":
    # 测试财务报表审计
    print("财务报表审计测试:")
    print(main(company_name="测试公司A", service_item="财务报表审计", amount=1000000))

    # 测试资本验证（货币）
    print("\n资本验证（货币）测试:")
    print(main(company_name="测试公司B", service_item="资本验证", amount=1500000, verification_type="货币"))

    # 测试资本验证（其他）
    print("\n资本验证（其他出资）测试:")
    print(main(company_name="测试公司C", service_item="资本验证", amount=1500000, verification_type="其他"))

    # 测试清产核资
    print("\n清产核资测试:")
    print(main(company_name="测试公司D", service_item="清产核资", amount=5000000))

    # 测试经济责任审计（多年）
    print("\n经济责任审计（4年）测试:")
    print(main(company_name="测试公司E", service_item="经济责任审计", amount=2000000, years=4))

    # 测试外汇收支审核（计时）
    print("\n外汇收支审核（计时）测试:")
    print(main(company_name="测试公司F", service_item="外汇收支审核",
               hours_by_level={"注册会计师": 5, "助理": 10}))

    # 测试医疗卫生机构审计
    print("\n医疗卫生机构审计测试:")
    print(main(company_name="某医院", service_item="医疗卫生机构审计", amount=100000000))