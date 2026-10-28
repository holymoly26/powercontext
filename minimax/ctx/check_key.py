"""API Key 自检：只打印掩码 + 一次最小调用结果，不泄露明文。

用法：python ctx/check_key.py
"""
import json
import sys

import requests

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from config import mask  # noqa: E402
import os  # noqa: E402

key = os.environ.get("MINIMAX_API_KEY", "")
group = os.environ.get("MINIMAX_GROUP_ID", "")
base = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
model = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")

print("API Key :", mask(key))
print("GroupID :", mask(group))
print("BaseURL :", base)
print("Model   :", model)
print()

if not key:
    print("❌ 未读到 MINIMAX_API_KEY，请先填写 .env")
    sys.exit(1)

url = base.rstrip("/") + "/text/chatcompletion_v2"
payload = {
    "model": model,
    "messages": [{"role": "user", "content": "只回复两个字：收到"}],
    "max_tokens": 16,
    "temperature": 0.1,
}

try:
    r = requests.post(
        url,
        headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    print("HTTP", r.status_code)
    try:
        data = r.json()
    except Exception:
        print(r.text[:300])
        sys.exit(2)
    base_resp = data.get("base_resp") or {}
    print("base_resp:", json.dumps(base_resp, ensure_ascii=False))
    choices = data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        print("回复内容:", (msg.get("content") or "")[:100])
    print("\n✅ 调用成功" if r.status_code == 200 and choices else "\n⚠️ 有响应但没有内容，请看上面的 base_resp")
except Exception as e:
    print("❌ 请求失败:", e)
    sys.exit(3)
