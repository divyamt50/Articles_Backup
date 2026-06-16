import asyncio
from cache import redis_client

async def main():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('new_articles')
    print("listening on 'new_articles'..... (Ctrl+C to stop)")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            print("New article event:", message["data"])


if __name__ == "__main__":
    asyncio.run(main())