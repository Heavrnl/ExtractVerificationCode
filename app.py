from flask import Flask, request, jsonify
import requests
import logging
from send_code import upload
from config import QWEN_URL, PROMPT_TEMPLATE, USE_AZURE_API, AZURE_ENDPOINT, AZURE_MODEL_NAME, GITHUB_TOKEN
import json

app = Flask(__name__)  # 创建 Flask 应用程序实例

def extract_code_local(text):
    url = QWEN_URL
    prompt_template = PROMPT_TEMPLATE
    headers = {"Content-Type": "application/json"}
    data = {"text": text, "prompt_template": prompt_template}

    response = requests.post(url, json=data, headers=headers)
    response_json = response.json()
    return response_json.get("response", "").split('\n')[0].strip()

def extract_code_azure(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }
    data = {
        "messages": [
            {"role": "system", "content": "从以下文本中提取验证码。只输出验证码，不要有任何其他文字。如果没有验证码，只输出'None'。"},
            {"role": "user", "content": text}
        ],
        "model": AZURE_MODEL_NAME,
        "temperature": 1,
        "max_tokens": 1000,
        "top_p": 1
    }
    response = requests.post(f"{AZURE_ENDPOINT}/chat/completions", headers=headers, json=data)
    response_json = response.json()
    return response_json['choices'][0]['message']['content'].strip()

@app.route('/evc', methods=['POST'])
def extract_verification_code():
    data = request.get_json()
    text = data.get('text')

    if USE_AZURE_API:
        verification_code = extract_code_azure(text)
    else:
        verification_code = extract_code_local(text)

    logging.info(f"verification_code:{verification_code}")
    if verification_code.lower() == 'none':
        return jsonify({"message": "No verification code found"}), 404

    upload(verification_code)
    return jsonify({"verification_code": verification_code})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5788,debug=True)