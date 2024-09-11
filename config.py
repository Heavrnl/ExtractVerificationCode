QWEN_URL = "http://qwen:5000/process"
PROMPT_TEMPLATE = "从以下文本中提取验证码。只输出验证码，不要有任何其他文字。如果没有验证码，只输出'None'。\n\n文本：{input_text}\n\n验证码："

# 新增配置项
USE_AZURE_API = True  # 设置为True时使用Azure API,False时使用本地LLM
AZURE_ENDPOINT = "https://models.inference.ai.azure.com"
AZURE_MODEL_NAME = "gpt-4o-mini"
GITHUB_TOKEN = ""
