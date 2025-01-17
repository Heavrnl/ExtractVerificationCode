import base64
import requests
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志级别
log_level = logging.INFO if os.getenv('DEBUG_MODE', 'false').lower() == 'true' else logging.ERROR
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 从环境变量获取配置
url = os.getenv('SYNC_URL')
username = os.getenv('SYNC_USERNAME')
token = os.getenv('SYNC_TOKEN')

logging.info(f"Sync URL: {url}")
logging.info(f"Sync Username: {username}")
logging.info(f"Sync Token: {'已设置' if token else '未设置'}")

# 构造认证头
auth_header = 'basic ' + base64.b64encode(f"{username}:{token}".encode()).decode()

# 处理 URL
url_without_slash = url.rstrip('/')
api_url = url_without_slash + '/SyncClipboard.json'

def upload(text):
    try:
        response = requests.put(
            api_url,
            headers={
                'authorization': auth_header,
                'Content-Type': 'application/json',
            },
            json={
                'File': '',
                'Clipboard': text,
                'Type': 'Text'
            }
        )
        response.raise_for_status()
        return response.json()  # 如果需要处理响应的话
    except requests.RequestException as e:
        logging.error(f"Upload failed: {e}")
        return None

