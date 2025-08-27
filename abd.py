import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def round_to_2_decimal(value):
    """精确到小数点2位的四舍五入"""
    decimal_value = Decimal(str(value))
    return float(decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate_financial_audit_fee(amount, return_details=False):
    """
    计算财务报表审计收费（阶梯式分段累进计费）

    收费标准（根据Excel表格）：
    - 0-50万元：2,000元（固定）
    - 50-100万元部分：该部分金额 × 0.200%
    - 100-500万元部分：该部分金额 × 0.090%
    - 500-1000万元部分：该部分金额 × 0.070%
    - 1000-5000万元部分：该部分金额 × 0.050%
    - 5000万元-1亿元部分：该部分金额 × 0.030%
    - 1-5亿元部分：该部分金额 × 0.015%
    - 5-10亿元部分：该部分金额 × 0.010%
    - 10亿元以上部分：该部分金额 × 0.008%

    例如：150万的计算 = 2000(50万固定) + 50万×0.2% + 50万×0.09% = 2000 + 1000 + 450 = 3450元
    """

    # 定义收费阶梯 收费标准定义
    brackets = [
        (500000, 2000, 0),  # 0-50万：固定2000元
        (1000000, 0, 0.002),  # 50-100万：0.2%
        (5000000, 0, 0.0009),  # 100-500万：0.09%
        (10000000, 0, 0.0007),  # 500-1000万：0.07%
        (50000000, 0, 0.0005),  # 1000-5000万：0.05%
        (100000000, 0, 0.0003),  # 5000万-1亿：0.03%
        (500000000, 0, 0.00015),  # 1-5亿：0.015%
        (1000000000, 0, 0.0001),  # 5-10亿：0.01%
        (float('inf'), 0, 0.00008)  # 10亿以上：0.008%
    ]

    total_fee = 0
    prev_limit = 0
    calculation_steps = []

    for upper_limit, fixed_fee, rate in brackets:
        if amount <= prev_limit:
            break

        # 计算本段的计费基数 也就是超出部分 segment_amount 这个阶段要计算的钱
        if amount <= upper_limit:
            segment_amount = amount - prev_limit
        else:
            segment_amount = upper_limit - prev_limit

        # 计算本段费用
        if fixed_fee > 0:  # 固定收费
            segment_fee = fixed_fee
            calculation_steps.append(f"0-{upper_limit / 10000:.0f}万元: {fixed_fee}元（固定）")
        else:  # 按比例收费
            segment_fee = segment_amount * rate
            if segment_amount > 0:
                calculation_steps.append(
                    f"{prev_limit / 10000:.0f}-{min(amount, upper_limit) / 10000:.0f}万元: "
                    f"{segment_amount / 10000:.0f}万 × {rate * 100:.3f}% = {segment_fee:.2f}元"
                )

        total_fee += segment_fee

        if amount <= upper_limit:
            break
        prev_limit = upper_limit

    result = round_to_2_decimal(total_fee)

    if return_details:
        return result, calculation_steps
    return result


def calculate_capital_verification_fee(amount, verification_type="货币", return_details=False):
    """
    计算资本验证收费（阶梯式分段累进计费）

    货币出资收费标准：
    - 0-50万元：1,200元（固定）
    - 50-100万元部分：该部分金额 × 0.150%
    - 100-500万元部分：该部分金额 × 0.040%
    - 500-1000万元部分：该部分金额 × 0.030%
    - 1000-5000万元部分：该部分金额 × 0.020%
    - 5000万元-1亿元部分：该部分金额 × 0.015%
    - 1-5亿元部分：该部分金额 × 0.010%
    - 5-10亿元部分：该部分金额 × 0.008%
    - 10亿元以上部分：该部分金额 × 0.006%

    其他出资：按货币出资方式收费标准的120%计收
    """

    # 定义收费阶梯
    brackets = [
        (500000, 1200, 0),  # 0-50万：固定1200元
        (1000000, 0, 0.0015),  # 50-100万：0.15%
        (5000000, 0, 0.0004),  # 100-500万：0.04%
        (10000000, 0, 0.0003),  # 500-1000万：0.03%
        (50000000, 0, 0.0002),  # 1000-5000万：0.02%
        (100000000, 0, 0.00015),  # 5000万-1亿：0.015%
        (500000000, 0, 0.0001),  # 1-5亿：0.01%
        (1000000000, 0, 0.00008),  # 5-10亿：0.008%
        (float('inf'), 0, 0.00006)  # 10亿以上：0.006%
    ]

    total_fee = 0
    prev_limit = 0
    calculation_steps = []

    for upper_limit, fixed_fee, rate in brackets:
        if amount <= prev_limit:
            break

        # 计算本段的计费基数
        if amount <= upper_limit:
            segment_amount = amount - prev_limit
        else:
            segment_amount = upper_limit - prev_limit

        # 计算本段费用
        if fixed_fee > 0:  # 固定收费
            segment_fee = fixed_fee
            calculation_steps.append(f"0-{upper_limit / 10000:.0f}万元: {fixed_fee}元（固定）")
        else:  # 按比例收费
            segment_fee = segment_amount * rate
            if segment_amount > 0:
                calculation_steps.append(
                    f"{prev_limit / 10000:.0f}-{min(amount, upper_limit) / 10000:.0f}万元: "
                    f"{segment_amount / 10000:.0f}万 × {rate * 100:.3f}% = {segment_fee:.2f}元"
                )

        total_fee += segment_fee

        if amount <= upper_limit:
            break
        prev_limit = upper_limit

    # 其他出资按120%计算
    if verification_type == "其他":
        calculation_steps.append(f"其他出资按120%计收: {total_fee:.2f} × 1.2 = {total_fee * 1.2:.2f}元")
        total_fee = total_fee * 1.2

    result = round_to_2_decimal(total_fee)

    if return_details:
        return result, calculation_steps
    return result


def calculate_medical_institution_audit_fee(amount, return_details=False):
    """
    计算医疗卫生机构等非盈利组织财务报表审计收费
    按财务报表审计标准的不同比例收费：
    - 1亿元以下部分：按财务报表审计标准下浮10%
    - 1-5亿元部分：按财务报表审计标准下浮20%
    - 5亿元以上部分：按财务报表审计标准下浮30%
    """

    calculation_steps = []

    # 先计算基础财务报表审计费用
    base_fee, base_steps = calculate_financial_audit_fee(amount, return_details=True)

    # 根据金额分段应用不同的折扣
    if amount <= 100000000:  # 1亿元以下，下浮10%
        final_fee = base_fee * 0.9
        calculation_steps.append(f"基础审计费: {base_fee:.2f}元")
        calculation_steps.append(f"1亿元以下部分下浮10%: {base_fee:.2f} × 0.9 = {final_fee:.2f}元")
    elif amount <= 500000000:  # 1-5亿元
        # 分段计算
        fee_1yi = calculate_financial_audit_fee(100000000)
        fee_above_1yi = base_fee - fee_1yi

        final_fee = fee_1yi * 0.9 + fee_above_1yi * 0.8
        calculation_steps.append(f"1亿元部分基础费: {fee_1yi:.2f} × 0.9 = {fee_1yi * 0.9:.2f}元")
        calculation_steps.append(f"1-5亿元部分基础费: {fee_above_1yi:.2f} × 0.8 = {fee_above_1yi * 0.8:.2f}元")
        calculation_steps.append(f"总计: {final_fee:.2f}元")
    else:  # 5亿元以上
        fee_1yi = calculate_financial_audit_fee(100000000)
        fee_1to5yi = calculate_financial_audit_fee(500000000) - fee_1yi
        fee_above_5yi = base_fee - calculate_financial_audit_fee(500000000)

        final_fee = fee_1yi * 0.9 + fee_1to5yi * 0.8 + fee_above_5yi * 0.7
        calculation_steps.append(f"1亿元部分: {fee_1yi * 0.9:.2f}元")
        calculation_steps.append(f"1-5亿元部分: {fee_1to5yi * 0.8:.2f}元")
        calculation_steps.append(f"5亿元以上部分: {fee_above_5yi * 0.7:.2f}元")
        calculation_steps.append(f"总计: {final_fee:.2f}元")

    result = round_to_2_decimal(final_fee)

    if return_details:
        return result, calculation_steps
    return result


def calculate_time_based_fee(hours_by_level, return_details=False):
    """
    计算计时收费
    收费标准（元/小时）：
    - 初级助理：300
    - 助理：600
    - 注册会计师：1000
    - 项目经理：1500
    - 部门经理：2000
    - 合伙人/主任会计师：3000
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
    calculation_steps = []

    for level, hours in hours_by_level.items():
        if level in rates and hours > 0:
            fee = rates[level] * hours
            total_fee += fee
            calculation_steps.append(f"{level}: {hours}小时 × {rates[level]}元/小时 = {fee}元")

    result = round_to_2_decimal(total_fee)

    if return_details:
        return result, calculation_steps
    return result


def get_service_unit(service_item):
    """获取服务项目的计费单位"""
    units = {
        "财务报表审计": "年",
        "投资移民审计": "年",
        "医疗卫生机构审计": "年",
        "非盈利组织审计": "年",
        "医疗卫生机构财务报表审计": "年",
        "资本验证": "次",
        "合并、分立、清算审计": "项",
        "合并分立清算审计": "项",
        "经济责任审计": "项",
        "清产核资": "项",
        "外汇收支审核": "项",
        "特殊目的审计": "项"
    }
    return units.get(service_item, "项")

##计算费用
def calculate_audit_fee(service_item, amount, **kwargs):
    """
    根据服务项目计算审计收费（含计算明细）
    years
    """

    return_details = kwargs.get("return_details", False)

    # 财务报表审计
    if service_item in ["财务报表审计", "投资移民审计"]:
        return calculate_financial_audit_fee(amount, return_details)

    # 资本验证
    elif service_item == "资本验证":
        verification_type = kwargs.get("verification_type", "货币")
        return calculate_capital_verification_fee(amount, verification_type, return_details)

    # 合并、分立、清算审计（按财务报表审计的150%，可多年累加）
    elif service_item in ["合并、分立、清算审计", "合并分立清算审计"]:
        base_fee = calculate_financial_audit_fee(amount)
        years = kwargs.get("years", 1)
        calculation_steps = []

        if years > 1:
            total_fee = 0
            for year in range(1, years + 1):
                if year <= 3:  # 前三年按150%
                    year_fee = base_fee * 1.5
                    calculation_steps.append(f"第{year}年: {base_fee:.2f} × 150% = {year_fee:.2f}元")
                else:  # 超过三年按120%
                    year_fee = base_fee * 1.2
                    calculation_steps.append(f"第{year}年: {base_fee:.2f} × 120% = {year_fee:.2f}元")
                total_fee += year_fee

            result = round_to_2_decimal(total_fee)
            if return_details:
                calculation_steps.append(f"合计: {result:.2f}元")
                return result, calculation_steps
            return result
        else:
            result = round_to_2_decimal(base_fee * 1.5)
            if return_details:
                return result, [f"财务报表审计基础费: {base_fee:.2f}元",
                                f"按150%计收: {base_fee:.2f} × 1.5 = {result:.2f}元"]
            return result

    # 经济责任审计（按财务报表审计的150%，可多年累加）
    elif service_item == "经济责任审计":
        base_fee = calculate_financial_audit_fee(amount)
        years = kwargs.get("years", 1)
        calculation_steps = []

        if years > 1:
            total_fee = 0
            for year in range(1, years + 1):
                if year <= 3:  # 前三年按150%
                    year_fee = base_fee * 1.5
                    calculation_steps.append(f"第{year}年: {base_fee:.2f} × 150% = {year_fee:.2f}元")
                else:  # 超过三年按120%
                    year_fee = base_fee * 1.2
                    calculation_steps.append(f"第{year}年: {base_fee:.2f} × 120% = {year_fee:.2f}元")
                total_fee += year_fee

            result = round_to_2_decimal(total_fee)
            if return_details:
                calculation_steps.append(f"合计: {result:.2f}元")
                return result, calculation_steps
            return result
        else:
            result = round_to_2_decimal(base_fee * 1.5)
            if return_details:
                return result, [f"财务报表审计基础费: {base_fee:.2f}元",
                                f"按150%计收: {result:.2f}元"]
            return result

    # 清产核资（按财务报表审计的200%）
    elif service_item == "清产核资":
        base_fee = calculate_financial_audit_fee(amount)
        result = round_to_2_decimal(base_fee * 2)
        if return_details:
            return result, [f"财务报表审计基础费: {base_fee:.2f}元",
                            f"按200%计收: {base_fee:.2f} × 2 = {result:.2f}元"]
        return result

    # 外汇收支审核（计时收费，最低1000元）
    elif service_item == "外汇收支审核":
        hours_by_level = kwargs.get("hours_by_level", {})
        if hours_by_level:
            fee, steps = calculate_time_based_fee(hours_by_level, return_details=True)
            result = max(1000, fee)
            if return_details:
                if result == 1000:
                    steps.append(f"最低收费: 1000元")
                return result, steps
            return result
        else:
            if return_details:
                return 1000, ["最低收费: 1000元"]
            return 1000

    # 特殊目的审计 按照4收费标准
    elif service_item == "特殊目的审计":
        base_fee = calculate_financial_audit_fee(amount)
        result = round_to_2_decimal(base_fee * 1.5)
        if return_details:
            return result, [f"参照经济责任审计标准（财务报表审计的150%）: {result:.2f}元"]
        return result

    # 医疗卫生机构等非盈利组织审计
    elif service_item in ["医疗卫生机构审计", "非盈利组织审计", "医疗卫生机构财务报表审计"]:
        return calculate_medical_institution_audit_fee(amount, return_details)

    # 默认按财务报表审计收费
    else:
        return calculate_financial_audit_fee(amount, return_details)


def main(company_name="公司名称", service_category="audit", service_item="财务报表审计",
         amount=0, amount_type="asset", special_requirements="", show_details=False, **kwargs) -> dict:
    """
    主函数：计算审计服务收费

    参数：
    - company_name: 客户名称
    - service_category: 服务类别
    - service_item: 服务项目名称
    - amount: 计费金额基数（单位：元）
    - amount_type: 金额类型（asset:资产总额, revenue:销售收入, capital:实收资本）
    - special_requirements: 特殊要求
    - show_details: 是否显示计算明细
    - kwargs: 其他参数（如verification_type验资类型、years年数、hours_by_level计时信息等）
    - unit 计算单位

    返回：
    包含收费信息的字典
    """

    # 确保金额为数字
    try:
        amount_value = float(amount)
    except (ValueError, TypeError):
        amount_value = 0

    # 获取计费单位
    service_unit = get_service_unit(service_item)

    # 计算收费（含明细）
    kwargs['return_details'] = True
    fee_result = calculate_audit_fee(service_item, amount_value, **kwargs)

    if isinstance(fee_result, tuple):
        fee_value, calculation_steps = fee_result
    else:
        fee_value = fee_result
        calculation_steps = []

    # 格式化金额和费用
    amount_str = f"{amount_value:,.0f}" if amount_value == int(amount_value) else f"{amount_value:,.2f}"
    fee_str = f"{fee_value:,.0f}" if fee_value == int(fee_value) else f"{fee_value:,.2f}"

    # 金额类型说明
    amount_type_desc = {
        "asset": "资产总额",
        "revenue": "销售收入",
        "capital": "实收资本"
    }

    # 构建返回结果
    result = {
        "company_name": str(company_name),
        "service_category": str(service_category),
        "service_item": str(service_item),
        "service_unit": service_unit,
        "amount": amount_str,
        "amount_type": amount_type_desc.get(amount_type, amount_type),
        "special_requirements": str(special_requirements),
        "fee": fee_str,
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "calculation_basis": "广东省会计师事务所审计服务收费标准"
    }

    # 添加计算明细（如果需要）
    if show_details and calculation_steps:
        result["calculation_details"] = calculation_steps

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
    print("=" * 60)
    print("广东省会计师事务所审计服务收费计算测试")
    print("=" * 60)

    # 测试1：财务报表审计 - 150万元
    print("\n【测试1】财务报表审计 - 150万元")
    result = main(
        company_name="测试公司A",
        service_item="财务报表审计",
        amount=1300000,
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")
    #
    # 测试2：资本验证（货币）- 300万元
    print("\n【测试2】资本验证（货币出资）- 300万元")
    result = main(
        company_name="测试公司B",
        service_item="资本验证",
        amount=3000000,
        amount_type="capital",
        verification_type="货币",
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"验资类型：{result['verification_type']}出资")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")

    # 测试3：资本验证（其他）- 300万元
    print("\n【测试3】资本验证（其他出资）- 300万元")
    result = main(
        company_name="测试公司C",
        service_item="资本验证",
        amount=3000000,
        amount_type="capital",
        verification_type="其他",
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"验资类型：{result['verification_type']}出资")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")

    # 测试4：清产核资 - 500万元
    print("\n【测试4】清产核资 - 500万元")
    result = main(
        company_name="测试公司D",
        service_item="清产核资",
        amount=5000000,
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元")
    print(f"收费金额：{result['fee']}元")

    # 测试5：经济责任审计（4年）- 200万元
    print("\n【测试5】经济责任审计（4年）- 200万元")
    result = main(
        company_name="测试公司E",
        service_item="经济责任审计",
        amount=2000000,
        years=4,
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"审计年数：{result['years']}年")
    print(f"计费基数：{result['amount']}元")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")

    # 测试6：外汇收支审核（计时）
    print("\n【测试6】外汇收支审核（计时收费）")
    result = main(
        company_name="测试公司F",
        service_item="外汇收支审核",
        hours_by_level={"注册会计师": 5, "助理": 10},
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"工时：{result['hours_breakdown']}")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")

    # 测试7：医疗卫生机构审计 - 1.5亿元
    print("\n【测试7】医疗卫生机构审计 - 1.5亿元")
    result = main(
        company_name="某医院",
        service_item="医疗卫生机构审计",
        amount=150000000,
        show_details=True
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元")
    print(f"收费金额：{result['fee']}元")

    print(result)