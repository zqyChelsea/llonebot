import redis
import json
import os

# Redis 配置
r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

# 读取群历史 JSON 文件
GROUP_ID = "222427909"
json_path = f"./data/group_history/{GROUP_ID}.json"

with open(json_path, "r", encoding="utf-8") as f:
    messages = json.load(f)

# 构造 Thread 结构
thread = {
    "id": GROUP_ID,
    "title": f"Group {GROUP_ID} Chat History",
    "subtitle": "",
    "status": "active",
    "createdAt": str(messages[-1]["time"]) if messages else "",
    "commentCount": len(messages),
    "riceScore": 0,
    "discordThreadId": "",
    "messages": []
}

for msg in messages:
    sender = msg.get("sender", {})
    thread["messages"].append({
        "id": str(msg.get("message_id", "")),
        "author": sender.get("nickname", "Unknown"),
        "time": str(msg.get("time", "")),
        "content": msg.get("raw_message", ""),
        "profile": sender.get("avatar_url", "")
    })

# 逐条发布到 Redis
for m in thread["messages"]:
    event = {
        "sender": m["author"],
        "messageId": m["id"],
        "message": m["content"],
        "profile": m["profile"]
    }
    body = {
        "platform": "qq",
        "channelID": GROUP_ID,
        "event": event
    }
    channel_name = f"integrations.qq-{GROUP_ID}"
    r.publish(channel_name, json.dumps(body, ensure_ascii=False))
    print(f"Published message to {channel_name}: {body}")

print("All messages published to Redis.")