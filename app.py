from flask import Flask, request, jsonify
from langchain_core.runnables import RunnableWithMessageHistory

from llm.chat import get_conversation_chain
from tax_audit.template_generation.accounting_template import generate_accounting_template
from utils.date_utils import parse_chinese_date
from utils.dify_api_utils import DifyApiUtils

app = Flask(__name__)


def format_dify_output_simple(outputs: dict) -> str:
    """
    简洁版本的格式化函数
    """
    company_name = outputs.get("company_name", "")
    service_item = outputs.get("service_item", "")
    calculation_details = outputs.get("calculation_details", [])
    data_url = outputs.get("data", "")

    # 简洁拼接
    calculation_text = "，".join(calculation_details) if calculation_details else "详见报价函"

    reply = f"公司名称：{company_name}，服务项目是：{service_item}，费用计算：{calculation_text}，报价函：{data_url}"

    return reply


def is_audit_related(message: str) -> bool:
    """
    判断是否为审计/税务相关请求，需要调用Dify工作流
    """
    # 审计和税务相关关键词
    audit_tax_keywords = [
        # 审计类
        "审计", "年审", "财务报表", "财务审计", "验资", "资本验证", "出资",
        "清算", "破产", "合并", "分立", "经济责任", "离任", "任期",
        "清产核资", "外汇", "外币", "专项", "特定目的",
        # 税务类
        "汇算清缴", "所得税申报", "年度申报", "亏损", "弥补",
        "资产损失", "报损", "损失扣除"
    ]

    # 检查消息中是否包含相关关键词
    return any(keyword in message for keyword in audit_tax_keywords)


def is_audit_related_llm(message: str) -> bool:
    """
    使用LLM判断是否为审计/税务相关请求
    """
    audit_check_prompt = f"""
请判断以下用户消息是否与审计或税务服务相关。

用户消息: {message}

审计服务包括：财务审计、年审、验资、清算审计、经济责任审计、清产核资、外汇收支审核、特殊目的审计等
税务服务包括：汇算清缴、所得税申报、亏损弥补鉴证、资产损失扣除鉴证等

请只回答：true 或 false
"""

    try:
        # 调用你的LLM API - 替换为实际的LLM调用
        # 示例：
        # llm_response = your_llm_client.chat(audit_check_prompt)
        #
        # 处理LLM响应，提取true/false
        # if "true" in llm_response.lower():
        #     return True
        # elif "false" in llm_response.lower():
        #     return False
        # else:
        #     # 如果LLM回答不清晰，fallback到关键词匹配
        #     return is_audit_related(message)

        # 临时使用关键词匹配（请替换为上面的LLM调用）
        return is_audit_related(message)

    except Exception as e:
        print(f"LLM判断出错，使用关键词匹配作为备选: {e}")
        return is_audit_related(message)
##普通聊天
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    message = data.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id 和 message 不能为空"}), 400

    # 判断是否需要调用Dify工作流
    if is_audit_related_llm(message):  # 使用LLM进行判断
        # 审计/税务相关请求 - 调用Dify工作流
        try:
            dify_client = DifyApiUtils()

            print(f"检测到审计/税务请求，调用Dify: {message}")

            # 直接将原始消息发送给Dify
            result = dify_client.workflow_run(
                user_input=message,
                user=user_id
            )

            if result and isinstance(result, dict) and "data" in result:
                outputs = result["data"]["outputs"]

                # 格式化Dify输出为友好的回复
                # format_dify_output() 为多行格式，format_dify_output_simple() 为单行格式
                reply = format_dify_output_simple(outputs)  # 默认使用简洁版本
                # reply = format_dify_output(outputs)  # 可选择多行版本

                return jsonify({
                    "reply": reply,
                    "type": "dify",
                    "workflow_id": result.get("workflow_id")
                })
            else:
                return jsonify({
                    "error": "Dify工作流执行失败",
                    "type": "dify_error"
                }), 500

        except Exception as e:
            print(f"调用Dify工作流出错: {e}")
            return jsonify({
                "error": f"审计服务暂时不可用: {str(e)}",
                "type": "dify_error"
            }), 500

    else:
        # 普通聊天请求 - 使用原有的对话链
        try:
            conversation = get_conversation_chain()

            response = conversation.invoke(
                {"input": message},
                config={"configurable": {"session_id": user_id}}
            )

            # 提取回复内容
            reply = response.content if hasattr(response, "content") else response["content"]

            return jsonify({
                "reply": reply,
                "type": "general"
            })

        except Exception as e:
            print(f"对话链执行出错: {e}")
            return jsonify({
                "error": f"服务暂时不可用: {str(e)}",
                "type": "general_error"
            }), 500

@app.route('/api/generate_template/accounting', methods=['POST'])
def api_accounting_generate_template():
    """
       API端点：生成会计模板
       请求体格式:
       {
           "company_name": "某某科技有限公司",
           "services": [
               {"name": "技术咨询服务", "total_fee": 50000.00},
               {"name": "系统开发服务", "total_fee": 100000.00}
           ],
           "year": 2024,
           "month": 12,
           "day": 10,
           "services_description": "2024年度财务报告"
       }

       V2.0 年月日合并格式：yyyy-mm-dd
       total_fee字符串格式接受，如json格式里面的"fee": "3,850",转成float
       """

    try:

        ##日期处理
        data = request.json

        date_str = data['date']

        year, month, day = parse_chinese_date(date_str)

        ##数值处理
        # 2. 处理services中的total_fee字符串格式
        services_processed = []
        for service in data.get('services', []):
            # 处理 total_fee: 去除逗号并转换为float
            total_fee_str = str(service.get('total_fee', '0'))

            # 去除可能的逗号、空格和货币符号
            total_fee_cleaned = total_fee_str.replace(',', '').replace(' ', '').replace('¥', '').replace('￥', '')

            try:
                total_fee_float = float(total_fee_cleaned)
            except ValueError:
                raise ValueError(f"服务 '{service.get('name', 'unknown')}' 的费用格式错误: {total_fee_str}")

            services_processed.append({
                'name': service.get('name'),
                'total_fee': total_fee_float
            })

        result = generate_accounting_template(
            company_name=data['company_name'],
            services_data_json=services_processed,  # 直接传入services数组
            year=year,
            month=month,
            day=day,
            services_description=data.get('services_description', '')
        )

        return jsonify({
            'status': 'success',
            'data': result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400



if __name__ == '__main__':
    app.run()
