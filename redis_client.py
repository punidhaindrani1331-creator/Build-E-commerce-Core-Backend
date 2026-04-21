import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")

# Initialize Redis client
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
