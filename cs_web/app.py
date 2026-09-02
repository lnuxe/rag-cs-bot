"""
无畏契约客服聊天 - 后端代理服务
将前端聊天请求转发到 Dify Chatflow API，规避 CORS 并隐藏 API Key。
用法: python3 app.py  (启动后访问 http://localhost:8000)
"""
import os
import re
import json
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="/")

# Dify 应用配置
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost/v1")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-u1HwALiH2uZv7RPjEYqE4m1E")

DIFY_CHAT_URL = f"{DIFY_BASE_URL}/chat-messages"


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """接收前端消息，转发到 Dify，返回客服回答"""
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    conversation_id = data.get("conversation_id") or ""
    user_id = data.get("user") or "web-user"

    if not query:
        return jsonify({"error": "消息不能为空"}), 400

    try:
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user_id,
        }
        resp = requests.post(
            DIFY_CHAT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()

        # 去掉 deepseek 模型的思考(thinking)部分，只保留最终回复。
        # deepseek 思考格式： 思考内容... response最终回答
        # 过滤顺序（从最通用到兜底）：
        #   1) " response" 标准分隔符（最常用）
        #   2) "<!--dify-deepseek-reasoning-->" Dify 注入的注释标记
        #   3) 行首 "response" 分隔符（后面跟空白或中文）
        answer = result.get("answer", "")
        answer = clean_answer(answer)

        return jsonify({
            "answer": answer,
            "conversation_id": result.get("conversation_id", ""),
            "message_id": result.get("message_id", ""),
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": "回答超时，请稍后再试"}), 504
    except Exception as e:
        return jsonify({"error": f"服务出错: {str(e)}"}), 500


def clean_answer(answer):
    """去掉 deepseek 模型的思考(thinking)部分，只保留最终回复。
    思考格式： 思考内容... response最终回答
    注意：
      - response 后的分隔空格可能是普通空格 U+0020，也可能是全角空格
        U+3000 / NBSP U+00A0，所以统一用正则 \\s* 匹配。
      - response 后可能紧跟中文，不能用 \\b 词边界（中文不属于 \\w）。
    """
    # 0) 优先：去掉以 "</thinking>" 结尾的思考块（DeepSeek 常见格式：
    #    思考内容\n</thinking>最终回答，此时无 response 分隔符，答案直接跟在 </thinking> 后）
    if "</thinking>" in answer:
        return answer.split("</thinking>", 1)[-1].strip()

    # 1) 任意空白 + "response" 分隔符（前后有空白界定，避免误伤普通词）
    #    匹配 " 空白 response 空白/中文 "，且 response 前面必须有空白分隔
    m = re.search(r"\s+response(?=\s|[\u4e00-\u9fa5<])", answer)
    if m:
        return answer[m.end():].strip()

    # 2) Dify 注入的 HTML 注释标记
    if "<!--dify-deepseek-reasoning-->" in answer:
        answer = answer.split("<!--dify-deepseek-reasoning-->", 1)[-1]

    # 3) 行首 "response" 分隔符
    match = re.search(r"(?m)^\s*response(?=\s|[\u4e00-\u9fa5])", answer)
    if match:
        answer = answer[match.end():].lstrip()
    elif answer.strip().startswith("response"):
        answer = answer.strip()[len("response"):].lstrip()

    return answer.strip()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"客服网页已启动: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)