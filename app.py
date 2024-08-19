from flask import Flask, request, jsonify, app
import requests
import logging
from send_code import upload
from config import QWEN_URL, PROMPT_TEMPLATE

app = Flask(__name__)  # 创建 Flask 应用程序实例

@app.route('/evc', methods=['POST'])
def extract_verification_code():
    data = request.get_json()
    text = data.get('text')

    url = QWEN_URL
    prompt_template = PROMPT_TEMPLATE
    headers = {"Content-Type": "application/json"}
    data = {"text": text,"prompt_template":prompt_template}

    response = requests.post(url, json=data, headers=headers)
    # 获取响应的文本内容
    response_text = response.text
    print(response_text)  # 打印响应文本，帮助调试
    # 解析JSON响应
    response_json = response.json()
    verification_code = response_json.get("response", "").split('\n')[0].strip()
    logging.info(f"verification_code:{verification_code}")
    if verification_code.lower() == 'none':
        return jsonify({"message": "No verification code found"}), 404  # 返回 404 Not Found

    upload(verification_code)
    return jsonify({"verification_code": verification_code})  # 返回找到的验证码

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5788,debug=True)