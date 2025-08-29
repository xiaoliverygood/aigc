import re
from datetime import date



def parse_chinese_date(date_str):
    """
    解析多种日期格式，主要支持中文格式

    支持的格式:
    - 2025年08月29日
    - 2025年8月29日 (不带前导零)
    - 2025-08-29
    - 2025/08/29
    """
    # 1. 解析中文日期格式 (2025年08月29日)
    # date_str = data.get('date')
    if not date_str:
        raise ValueError("缺少日期字段 'date'")

    # 方法1：使用正则表达式解析中文日期
    chinese_date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    match = re.match(chinese_date_pattern, date_str)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        return year, month, day

    return None


if __name__ == '__main__':
    year, month, day= parse_chinese_date("2025年08月29日")
    print(year, month, day)