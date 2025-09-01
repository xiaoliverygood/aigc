import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def round_to_2_decimal(value):
    """精确到小数点2位的四舍五入"""
    decimal_value = Decimal(str(value))
    return float(decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def calculate_income_tax_filing_fee(amount, return_details=False):
    """
    计算企业所得税汇算清缴纳税申报鉴证收费（阶梯式分段累进计费）

    收费标准（按营业收入或资产总额）：
    - 不超过100万元：0.3%，下限3000元
    - 100-500万元部分：该部分金额 × 0.1%
    - 500-1000万元部分：该部分金额 × 0.05%
    - 1000-5000万元部分：该部分金额 × 0.03%
    - 5000万-1亿元部分：该部分金额 × 0.02%
    - 1-5亿元部分：该部分金额 × 0.01%
    - 5-10亿元部分：该部分金额 × 0.005%
    - 10亿元以上部分：该部分金额 × 0.002%
    """

    # 定义收费阶梯
    brackets = [
        (1000000, 3000, 0.003),  # 不超过100万：0.3%，下限3000元
        (5000000, 0, 0.001),  # 100-500万：0.1%
        (10000000, 0, 0.0005),  # 500-1000万：0.05%
        (50000000, 0, 0.0003),  # 1000-5000万：0.03%
        (100000000, 0, 0.0002),  # 5000万-1亿：0.02%
        (500000000, 0, 0.0001),  # 1-5亿：0.01%
        (1000000000, 0, 0.00005),  # 5-10亿：0.005%
        (float('inf'), 0, 0.00002)  # 10亿以上：0.002%
    ]

    total_fee = 0
    prev_limit = 0
    calculation_steps = []

    for upper_limit, min_fee, rate in brackets:
        if amount <= prev_limit:
            break

        # 计算本段的计费基数
        if amount <= upper_limit:
            segment_amount = amount - prev_limit
        else:
            segment_amount = upper_limit - prev_limit

        # 计算本段费用
        segment_fee = segment_amount * rate

        # 第一档有最低收费限制
        if prev_limit == 0 and min_fee > 0:
            segment_fee = max(segment_fee, min_fee)
            calculation_steps.append(
                f"0-{upper_limit / 10000:.0f}万元: {segment_amount / 10000:.0f}万 × {rate * 100:.3f}% = {segment_amount * rate:.2f}元，"
                f"按最低收费{min_fee}元计算"
            )
        else:
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


def calculate_asset_loss_fee(amount, return_details=False):
    """
    计算企业资产损失所得税前扣除鉴证收费（阶梯式分段累进计费）

    收费标准（按报损金额）：
    - 不超过100万元：1%，下限10000元
    - 100-500万元部分：该部分金额 × 0.5%
    - 500-1000万元部分：该部分金额 × 0.3%
    - 1000-5000万元部分：该部分金额 × 0.2%
    - 5000万-1亿元部分：该部分金额 × 0.1%
    - 1-5亿元部分：该部分金额 × 0.05%
    - 5-10亿元部分：该部分金额 × 0.03%
    - 10亿元以上部分：该部分金额 × 0.01%
    """

    # 定义收费阶梯
    brackets = [
        (1000000, 10000, 0.01),  # 不超过100万：1%，下限10000元
        (5000000, 0, 0.005),  # 100-500万：0.5%
        (10000000, 0, 0.003),  # 500-1000万：0.3%
        (50000000, 0, 0.002),  # 1000-5000万：0.2%
        (100000000, 0, 0.001),  # 5000万-1亿：0.1%
        (500000000, 0, 0.0005),  # 1-5亿：0.05%
        (1000000000, 0, 0.0003),  # 5-10亿：0.03%
        (float('inf'), 0, 0.0001)  # 10亿以上：0.01%
    ]

    total_fee = 0
    prev_limit = 0
    calculation_steps = []

    for upper_limit, min_fee, rate in brackets:
        if amount <= prev_limit:
            break

        # 计算本段的计费基数
        if amount <= upper_limit:
            segment_amount = amount - prev_limit
        else:
            segment_amount = upper_limit - prev_limit

        # 计算本段费用
        segment_fee = segment_amount * rate

        # 第一档有最低收费限制
        if prev_limit == 0 and min_fee > 0:
            segment_fee = max(segment_fee, min_fee)
            calculation_steps.append(
                f"0-{upper_limit / 10000:.0f}万元: {segment_amount / 10000:.0f}万 × {rate * 100:.1f}% = {segment_amount * rate:.2f}元，"
                f"按最低收费{min_fee}元计算"
            )
        else:
            if segment_amount > 0:
                calculation_steps.append(
                    f"{prev_limit / 10000:.0f}-{min(amount, upper_limit) / 10000:.0f}万元: "
                    f"{segment_amount / 10000:.0f}万 × {rate * 100:.2f}% = {segment_fee:.2f}元"
                )

        total_fee += segment_fee

        if amount <= upper_limit:
            break
        prev_limit = upper_limit

    result = round_to_2_decimal(total_fee)

    if return_details:
        return result, calculation_steps
    return result


def calculate_land_value_added_tax_fee(amount, return_details=False):
    """
    计算土地增值税清算鉴证收费（阶梯式分段累进计费）

    收费标准（按项目收入或扣除项目金额）：
    - 不超过5000万元：最低收费5万元
    - 5000万-1亿元部分：该部分金额 × 0.08%
    - 1-5亿元部分：该部分金额 × 0.07%
    - 5-10亿元部分：该部分金额 × 0.06%
    - 10亿元以上部分：该部分金额 × 0.05%
    """

    # 定义收费阶梯
    brackets = [
        (50000000, 50000, 0),  # 不超过5000万：最低50000元
        (100000000, 0, 0.0008),  # 5000万-1亿：0.08%
        (500000000, 0, 0.0007),  # 1-5亿：0.07%
        (1000000000, 0, 0.0006),  # 5-10亿：0.06%
        (float('inf'), 0, 0.0005)  # 10亿以上：0.05%
    ]

    total_fee = 0
    prev_limit = 0
    calculation_steps = []

    for upper_limit, min_fee, rate in brackets:
        if amount <= prev_limit:
            break

        # 计算本段的计费基数
        if amount <= upper_limit:
            segment_amount = amount - prev_limit
        else:
            segment_amount = upper_limit - prev_limit

        # 计算本段费用
        if min_fee > 0:  # 第一档有最低收费
            segment_fee = min_fee
            calculation_steps.append(f"0-{upper_limit / 10000:.0f}万元: 最低收费{min_fee}元")
        else:  # 按比例收费
            segment_fee = segment_amount * rate
            if segment_amount > 0:
                calculation_steps.append(
                    f"{prev_limit / 10000:.0f}-{min(amount, upper_limit) / 10000:.0f}万元: "
                    f"{segment_amount / 10000:.0f}万 × {rate * 100:.2f}% = {segment_fee:.2f}元"
                )

        total_fee += segment_fee

        if amount <= upper_limit:
            break
        prev_limit = upper_limit

    result = round_to_2_decimal(total_fee)

    if return_details:
        return result, calculation_steps
    return result


def calculate_tax_time_based_fee(hours_by_level, return_details=False):
    """
    计算涉税鉴证业务计时收费
    收费标准（元/小时）：
    - 助理人员：200-500元/小时（取中位数350元）
    - 项目负责人：500-1000元/小时（取中位数750元）
    - 部门经理：1000-1500元/小时（取中位数1250元）
    - 注册税务师（合伙人）：1500-2500元/小时（取中位数2000元）
    """
    rates = {
        "助理人员": 350,
        "助理": 350,
        "项目负责人": 750,
        "项目经理": 750,
        "部门经理": 1250,
        "注册税务师": 2000,
        "合伙人": 2000
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


def calculate_tax_service_fee(service_item, amount, years=None, hours_by_level=None, return_details=False):
    """
    根据服务项目计算税务服务收费（含计算明细）
    """

    # 企业所得税汇算清缴纳税申报鉴证
    if service_item in ["企业所得税汇算清缴纳税申报鉴证", "企业所得税汇算清缴"]:
        return calculate_income_tax_filing_fee(amount, return_details)

    # 企业所得税税前弥补亏损鉴证
    elif service_item in ["企业所得税税前弥补亏损鉴证", "税前弥补亏损鉴证"]:
        years = years or 1
        base_fee = calculate_income_tax_filing_fee(amount)
        total_fee = base_fee * years

        calculation_steps = []
        if years > 1:
            for year in range(1, years + 1):
                calculation_steps.append(f"第{year}个亏损年度: {base_fee:.2f}元")
            calculation_steps.append(f"合计{years}个年度: {total_fee:.2f}元")
        else:
            calculation_steps.append(f"参照企业所得税汇算清缴标准: {base_fee:.2f}元")

        result = round_to_2_decimal(total_fee)

        if return_details:
            return result, calculation_steps
        return result

    # 企业资产损失所得税前扣除鉴证
    elif service_item in ["企业资产损失所得税前扣除鉴证", "资产损失扣除鉴证"]:
        return calculate_asset_loss_fee(amount, return_details)

    # 土地增值税清算鉴证
    elif service_item in ["土地增值税清算鉴证", "土地增值税清算"]:
        return calculate_land_value_added_tax_fee(amount, return_details)

    # 计时收费
    elif service_item in ["计时收费", "其他涉税鉴证"]:
        if hours_by_level:
            return calculate_tax_time_based_fee(hours_by_level, return_details)
        else:
            if return_details:
                return 0, ["请提供各级别人员工时"]
            return 0

    # 默认按企业所得税汇算清缴收费
    else:
        return calculate_income_tax_filing_fee(amount, return_details)


def get_tax_service_unit(service_item):
    """获取税务服务项目的计费单位"""
    units = {
        "企业所得税汇算清缴纳税申报鉴证": "年",
        "企业所得税汇算清缴": "年",
        "企业所得税税前弥补亏损鉴证": "年",
        "税前弥补亏损鉴证": "年",
        "企业资产损失所得税前扣除鉴证": "项",
        "资产损失扣除鉴证": "项",
        "土地增值税清算鉴证": "项",
        "土地增值税清算": "项",
        "计时收费": "项",
        "其他涉税鉴证": "项"
    }
    return units.get(service_item, "项")


def main(service_item: str, amount: str, years: str = None, hours_by_level: str = None,
         company_name: str = "公司名称", amount_type: str = "revenue",
         special_requirements: str = "", show_details: str = "true") -> dict:
    """
    主函数：计算税务服务收费

    参数：
    - service_item: 服务项目名称
    - amount: 计费金额基数（单位：元）
    - years: 亏损年度数量（用于税前弥补亏损鉴证）
    - hours_by_level: 各级别工时字典的JSON字符串（用于计时收费）
    - company_name: 客户名称
    - amount_type: 金额类型（revenue:营业收入, asset:资产总额, loss_amount:报损金额, project_income:项目收入）
    - special_requirements: 特殊要求
    - show_details: 是否显示计算明细

    返回：
    包含收费信息的字典
    """

    # 参数处理
    try:
        amount_value = float(amount)
    except (ValueError, TypeError):
        amount_value = 0

    try:
        years_value = int(years) if years else None
    except (ValueError, TypeError):
        years_value = None

    try:
        hours_dict = json.loads(hours_by_level) if hours_by_level else None
    except (json.JSONDecodeError, TypeError):
        hours_dict = None

    show_details_bool = str(show_details).lower() == "true"

    # 获取计费单位
    service_unit = get_tax_service_unit(service_item)

    # 计算收费（含明细）
    fee_result = calculate_tax_service_fee(
        service_item=service_item,
        amount=amount_value,
        years=years_value,
        hours_by_level=hours_dict,
        return_details=True
    )

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
        "revenue": "营业收入",
        "asset": "资产总额",
        "loss_amount": "报损金额",
        "project_income": "项目收入"
    }

    # 构建返回结果
    result = {
        "company_name": str(company_name),
        "service_category": "涉税鉴证业务",
        "service_item": str(service_item),
        "service_unit": service_unit,
        "amount": amount_str,
        "amount_type": amount_type_desc.get(amount_type, amount_type),
        "special_requirements": str(special_requirements),
        "fee": fee_str,
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "calculation_basis": "广东省税务师事务所涉税鉴证业务收费标准"
    }

    # 添加计算明细（如果需要）
    if show_details_bool and calculation_steps:
        result["calculation_details"] = calculation_steps

    # 添加额外参数到结果中（如有）
    if years_value:
        result["years"] = str(years_value)
    if hours_dict:
        result["hours_breakdown"] = hours_dict

    return result


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("广东省税务师事务所涉税鉴证业务收费计算测试")
    print("=" * 60)

    # 测试1：企业所得税汇算清缴 - 150万元营业收入
    print("\n【测试1】企业所得税汇算清缴 - 150万元营业收入")
    result = main(
        service_item="企业所得税汇算清缴纳税申报鉴证",
        amount="1500000",
        company_name="测试公司A",
        amount_type="revenue"
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")

    print(result)

    # 测试2：资产损失扣除鉴证 - 300万元报损金额
    print("\n【测试2】企业资产损失所得税前扣除鉴证 - 300万元报损金额")
    result = main(
        service_item="企业资产损失所得税前扣除鉴证",
        amount="3000000",
        company_name="测试公司B",
        amount_type="loss_amount"
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")
    # 测试3：土地增值税清算 - 8000万元项目收入
    print("\n【测试3】土地增值税清算鉴证 - 8000万元项目收入")
    result = main(
        service_item="土地增值税清算鉴证",
        amount="80000000",
        company_name="测试房地产公司",
        amount_type="project_income"
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"计费基数：{result['amount']}元（{result['amount_type']}）")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")
    # 测试4：税前弥补亏损鉴证（3个年度）
    print("\n【测试4】企业所得税税前弥补亏损鉴证（3个年度）- 200万元")
    result = main(
        service_item="企业所得税税前弥补亏损鉴证",
        amount="2000000",
        years="3",
        company_name="测试公司D"
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"亏损年度：{result['years']}年")
    print(f"计费基数：{result['amount']}元")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")
    # 测试5：计时收费
    print("\n【测试5】涉税鉴证业务计时收费")
    hours_data = '{"注册税务师": 8, "项目负责人": 12, "助理人员": 20}'
    result = main(
        service_item="计时收费",
        amount="0",
        hours_by_level=hours_data,
        company_name="测试公司E"
    )
    print(f"客户：{result['company_name']}")
    print(f"服务：{result['service_item']}（{result['service_unit']}）")
    print(f"工时分配：{result['hours_breakdown']}")
    print(f"收费金额：{result['fee']}元")
    if 'calculation_details' in result:
        print("计算明细：")
        for step in result['calculation_details']:
            print(f"  - {step}")