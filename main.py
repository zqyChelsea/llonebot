import argparse
from chat_service import LLOneBotChatHistoryFetcher, RedisPublisher, Thread, Message
import os
import json

# 命令行参数解析
def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and publish QQ group chat history via LLOneBot and Redis.")
    parser.add_argument('--group_id', type=str, required=True, help='QQ群号')
    parser.add_argument('--api_url', type=str, default='http://localhost:3000/get_group_msg_history', help='LLOneBot HTTP API地址')
    parser.add_argument('--redis_host', type=str, default='127.0.0.1', help='Redis主机')
    parser.add_argument('--redis_port', type=int, default=6379, help='Redis端口')
    parser.add_argument('--count', type=int, default=100, help='获取消息条数')
    return parser.parse_args()

def main():
    args = parse_args()
    fetcher = LLOneBotChatHistoryFetcher(args.api_url)
    publisher = RedisPublisher(args.redis_host, args.redis_port)
    try:
        messages = fetcher.fetch_group_history(args.group_id, count=args.count)
    except Exception as e:
        print(f"获取群聊历史失败: {e}")
        return
    thread = Thread(
        id=args.group_id,
        title=f"Group {args.group_id} Chat History",
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
    publisher.publish_thread(args.group_id, thread)
    print(f"已获取并发布群 {args.group_id} 的最新{args.count}条消息到 Redis。")

    # 保存为json文件，格式为消息数组，包含所有原始字段和readable_time
    save_dir = "./data/group_history"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f"{args.group_id}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"已保存群 {args.group_id} 的消息到 {save_path}")

if __name__ == "__main__":
    main() 