from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import redis
import os
import json
from datetime import datetime

# 配置
LLOBOT_API_URL = "http://localhost:3000/get_group_msg_history"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
GROUP_ID = "222427909"  # 可根据实际需求动态传参

# FastAPI 实例
app = FastAPI()

class Message(BaseModel):
    id: str
    author: str
    time: str
    content: str
    profile: str = ""

class Thread(BaseModel):
    id: str
    title: str
    subtitle: str
    status: str
    createdAt: str
    commentCount: int
    riceScore: int
    discordThreadId: str
    messages: List[Message]

class LLOneBotChatHistoryFetcher:
    def __init__(self, api_url: str):
        self.api_url = api_url

    def fetch_group_history(self, group_id: str, message_seq: int = 0, count: int = 100) -> List[dict]:
        payload = {
            "group_id": int(group_id),
            "message_seq": message_seq,
            "count": count
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=10)
            data = resp.json()
            if data.get("status") == "ok":
                messages = data["data"]["messages"]
                for msg in messages:
                    ts = msg.get("time", 0)
                    msg["readable_time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                return messages
            else:
                raise Exception(f"API error: {data.get('msg')}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch group history: {e}")

class RedisPublisher:
    def __init__(self, host: str, port: int):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def publish_message(self, group_id: str, message: dict):
        event = {
            "sender": message["author"],
            "messageId": message["id"],
            "message": message["content"],
            "profile": message["profile"]
        }
        body = {
            "platform": "qq",
            "channelID": group_id,
            "event": event
        }
        channel_name = f"integrations.qq-{group_id}"
        self.r.publish(channel_name, json.dumps(body, ensure_ascii=False))

    def publish_thread(self, group_id: str, thread: Thread):
        for m in thread.messages:
            self.publish_message(group_id, m.dict())

# 实例化服务
fetcher = LLOneBotChatHistoryFetcher(LLOBOT_API_URL)
publisher = RedisPublisher(REDIS_HOST, REDIS_PORT)

@app.get("/group/{group_id}/history", response_model=Thread)
def get_and_publish_group_history(group_id: str):
    """
    获取最近100条群聊记录，并实时发布到 Redis。
    """
    try:
        messages = fetcher.fetch_group_history(group_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    thread = Thread(
        id=group_id,
        title=f"Group {group_id} Chat History",
        subtitle="",
        status="active",
        createdAt=messages[-1]["readable_time"] if messages else "",
        commentCount=len(messages),
        riceScore=0,
        discordThreadId="",
        messages=[
            Message(
                id=str(msg.get("message_id", "")),
                author=msg.get("sender", {}).get("nickname", "Unknown"),
                time=msg.get("readable_time", ""),
                content=msg.get("raw_message", ""),
                profile=""
            ) for msg in messages
        ]
    )
    publisher.publish_thread(group_id, thread)
    return thread 