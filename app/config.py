import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DEEPINFRA_TOKEN: str = os.getenv("DEEPINFRA_TOKEN", "")
    DEEPINFRA_API_URL: str = "https://api.deepinfra.com/v1/openai/chat/completions"
    MODEL_NAME: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    MAX_CONCURRENT_REQUESTS: int = 300  # Tăng từ 120 lên 300
    
    # Redis settings - Optimized for high throughput
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "50"))  # Connection pool size
    CACHE_TTL: int = 5 * 60 * 60  # 5 hours in seconds
    
    # Performance settings
    ENABLE_BATCH_PROCESSING: bool = os.getenv("ENABLE_BATCH_PROCESSING", "true").lower() == "true"
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "50"))
    MEMORY_CACHE_SIZE: int = int(os.getenv("MEMORY_CACHE_SIZE", "10000"))
    
settings = Settings()