from flask import Flask, request, jsonify
import requests
import logging
from send_code import upload
from config import QWEN_URL, PROMPT_TEMPLATE, USE_AZURE_API, AZURE_ENDPOINT, AZURE_MODEL_NAME, GITHUB_TOKEN
import json
import re

app = Flask(__name__)  # 创建 Flask 应用程序实例

# 将关键词列表单独定义
VERIFICATION_KEYWORDS = [
    "验证码", "校验码", "检验码", "确认码", "激活码", "动态码", "安全码",
    "验证代码", "校验代码", "检验代码", "激活代码", "确认代码", "动态代码", "安全代码",
    "登入码", "认证码", "识别码", "短信口令", "动态密码", "交易码", "上网密码", "随机码", "动态口令",
    "驗證碼", "校驗碼", "檢驗碼", "確認碼", "激活碼", "動態碼",
    "驗證代碼", "校驗代碼", "檢驗代碼", "確認代碼", "激活代碼", "動態代碼",
    "登入碼", "認證碼", "識別碼",
    "code", "otp", "one-time password", "verification", "auth", "authentication",
    "pin", "security", "access", "token",
    "短信验证", "短信验證", "短信校验", "短信校驗",
    "手机验证", "手機驗證", "手机校验", "手機校驗",
    "验证短信", "驗證短信", "验证信息", "驗證信息",
    "一次性密码", "一次性密碼", "临时密码", "臨時密碼",
    "授权码", "授權碼", "授权密码", "授權密碼",
    "二步验证", "二步驗證", "两步验证", "兩步驗證",
    "mfa", "2fa", "two-factor", "multi-factor",
    "passcode", "pass code", "secure code", "security code",
    "tac", "tan", "transaction authentication number",
    "验证信息", "驗證信息", "验证短信", "驗證短信",
    "验证邮件", "驗證郵件", "确认邮件", "確認郵件",
    "一次性验证码", "一次性驗證碼", "单次有效", "單次有效",
    "临时口令", "臨時口令", "临时验证码", "臨時驗證碼"
]

def desensitize_text(text):
    # 脱敏处理 IP 地址、链接、手机号码、邮箱、信用卡号码
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '***.***.***.***', text)  # 替换 IP 地址
    text = re.sub(r'http[s]?://\S+', 'http://****', text)  # 替换 URL
    text = re.sub(r'\b\d{10,11}\b', '**********', text)  # 替换手机号码
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '****@****.***', text)  # 替换邮箱
    text = re.sub(r'\b\d{13,19}\b', '********************', text)  # 替换信用卡号码
    return text

def contains_verification_keywords(text):
    # 将关键词列表转换为正则表达式模式
    pattern = r'\b(' + '|'.join(re.escape(keyword) for keyword in VERIFICATION_KEYWORDS) + r')\b'
    # 编译正则表达式
    regex = re.compile(pattern, re.IGNORECASE)
    
    # 使用正则表达式搜索
    return bool(regex.search(text))

def extract_code_local(text):
    text = desensitize_text(text)  # 脱敏处理
    url = QWEN_URL
    prompt_template = PROMPT_TEMPLATE
    headers = {"Content-Type": "application/json"}
    data = {"text": text, "prompt_template": prompt_template}

    response = requests.post(url, json=data, headers=headers)
    response_json = response.json()
    return response_json.get("response", "").split('\n')[0].strip()

def extract_code_azure(text):
    text = desensitize_text(text)  # 脱敏处理
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

    if not contains_verification_keywords(text):
        return jsonify({"message": "No verification code keywords found"}), 400

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
