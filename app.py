from flask import Flask, request, jsonify
from langchain_core.runnables import RunnableWithMessageHistory

from llm.chat import get_conversation_chain

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


if __name__ == '__main__':
    app.run()
