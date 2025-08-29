from flask import Flask, request, jsonify
from langchain_core.runnables import RunnableWithMessageHistory

from llm.chat import get_conversation_chain
from tax_audit.template_generation.accounting_template import generate_accounting_template

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
       """

    try:
        data = request.json

        result = generate_accounting_template(
            company_name=data['company_name'],
            services_data_json=data['services'],  # 直接传入services数组
            year=data['year'],
            month=data['month'],
            day=data['day'],
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
