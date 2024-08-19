import base64
import requests

# User Config
url = 'url'
username = 'username'
token = 'token'

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
        print(f"Upload failed: {e}")
        return None

