QWEN_URL = "http://qwen:5000/process"
PROMPT_TEMPLATE = "从以下文本中提取验证码。只输出验证码，不要有任何其他文字。如果没有验证码，只输出'None'。\n\n文本：{input_text}\n\n验证码："