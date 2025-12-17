from flask import Flask, request, jsonify
import requests
import logging
from send_code import upload
import re
from dotenv import load_dotenv
import os
import google.generativeai as genai
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 根据DEBUG_MODE设置日志级别
log_level = logging.INFO if os.getenv('DEBUG_MODE', 'false').lower() == 'true' else logging.ERROR
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


app = Flask(__name__) 

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
    # 简化匹配逻辑，直接检查关键词是否在文本中，不区分大小写
    text = text.lower()
    return any(keyword.lower() in text for keyword in VERIFICATION_KEYWORDS)

def extract_code_llm(text):
    """使用 OpenAI 兼容 API 提取验证码"""
    text = desensitize_text(text)
    prompt_template = os.getenv('PROMPT_TEMPLATE')
    prompt = prompt_template.format(input_text=text)
    
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL')
        )
        
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL'),
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=1,
            max_tokens=1000,
            top_p=1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"LLM API error: {e}")
        return "None"

def extract_code_local(text):
    """使用正则表达式匹配验证码
    常见的验证码模式：
    1. 4-6位纯数字
    2. 4-8位数字字母混合
    3. 前后可能带有特定文字标记
    """
    # 对文本进行脱敏处理
    text = desensitize_text(text)
    
    # 常见验证码模式的正则表达式
    patterns = [
        # 前后带验证码字样的4-6位纯数字
        r'(?:验证码|校验码|确认码|动态码|验证代码|码|code|Code).{0,4}?(\d{4,6})\D',
        # 前后带验证码字样的4-8位数字字母混合
        r'(?:验证码|校验码|确认码|动态码|验证代码|码|code|Code).{0,4}?([0-9a-zA-Z]{4,8})\D',
        # 单独的4-6位纯数字
        r'\D(\d{4,6})\D',
        # 单独的4-8位数字字母混合
        r'\D([0-9a-zA-Z]{4,8})\D'
    ]
    
    # 依次尝试各种模式
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # 返回第一个匹配到的验证码
            return match.group(1)
    
    # 如果没有找到验证码，返回None
    return "None"



@app.route('/evc', methods=['POST'])
def extract_verification_code():
    data = request.get_json()
    text = data.get('text')
    
    logging.info(f"收到文本: {text}")

    if not contains_verification_keywords(text):
        logging.info("未找到验证码关键词")
        return jsonify({"message": "No verification code keywords found"}), 400

    use_local = os.getenv('USE_LOCAL', 'false').lower() == 'true'
    
    logging.info(f"当前配置 - 本地提取: {use_local}")
    verification_code = "None"
    
    # 如果启用了本地匹配，先尝试本地匹配
    if use_local:
        logging.info("尝试本地正则匹配...")
        verification_code = extract_code_local(text)
        logging.info(f"本地匹配结果: {verification_code}")
    # 如果本地匹配没有结果，使用 LLM API
    if verification_code == "None":
        logging.info("尝试使用 LLM API...")
        verification_code = extract_code_llm(text)
        logging.info(f"LLM API结果: {verification_code}")

    logging.info(f"最终提取的验证码: {verification_code}")
    
    if verification_code.lower() == 'none':
        return jsonify({"message": "No verification code found"}), 404

    upload(verification_code)
    return jsonify({"verification_code": verification_code})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5788, debug=True)
