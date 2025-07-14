import os
import json
import requests
from datetime import datetime

# LLOneBot HTTP API地址
API_URL = "http://localhost:3000/get_group_msg_history"

# 目标QQ群号（请替换为你的群号）
GROUP_ID = 222427909

# 起始消息序号（0表示最新消息）
MESSAGE_SEQ = 0

payload = {
    "group_id": GROUP_ID,
    "message_seq": MESSAGE_SEQ
}

try:
    response = requests.post(API_URL, json=payload, timeout=10)
    result = response.json()
except Exception as e:
    print(f"请求失败: {e}")
    exit(1)

if result.get("status") == "ok":
    messages = result["data"]["messages"]
    # 保存路径
    save_dir = "./data/group_history"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{GROUP_ID}.json")
    # 格式化时间戳
    for msg in messages:
        ts = msg.get("time", 0)
        msg["readable_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"群消息已保存到: {save_path}")
else:
    print(f"获取消息失败，错误信息: {result.get('msg')}")