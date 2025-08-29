from flask import Flask, request, jsonify
from langchain_core.runnables import RunnableWithMessageHistory

from llm.chat import get_conversation_chain
from tax_audit.template_generation.accounting_template import generate_accounting_template
from utils.date_utils import parse_chinese_date

app = Flask(__name__)

##普通聊天
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    message = data.get("message")
    if not user_id or not message:
        return jsonify({"error": "user_id 和 message 不能为空"}), 400

    conversation = get_conversation_chain()


    # if message
    response = conversation.invoke(
        {"input": message},
        config={"configurable": {"session_id": user_id}}  # 必须传会话ID
    )

    # 这里 response 是字典，取 content
    reply = response.content if hasattr(response, "content") else response["content"]

    return jsonify({"reply": reply})

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
