import asyncio
import random
import json
import hashlib
from typing import Optional, Dict, Any, List
import httpx
import redis.asyncio as redis
from functools import lru_cache
import time

from app.config import settings
from app.models import SpamRequest


class OptimizedSpamDetector:
    def __init__(self):
        # Tăng concurrent requests
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS * 2)
        
        # Tối ưu HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),  # Giảm timeout
            limits=httpx.Limits(
                max_connections=settings.MAX_CONCURRENT_REQUESTS * 4,
                max_keepalive_connections=settings.MAX_CONCURRENT_REQUESTS * 3,
            ),
            http2=True,  # Enable HTTP/2
        )
        
        # Redis connection pool
        self.redis_pool = None
        self._redis_lock = asyncio.Lock()
        
        # In-memory cache cho hot data
        self._memory_cache: Dict[str, tuple[bool, float]] = {}
        self._memory_cache_size = 10000
        self._memory_cache_ttl = 300  # 5 minutes
        
        # Batch processing
        self._batch_queue = asyncio.Queue(maxsize=1000)
        self._batch_results = {}
        self._batch_processor_task = None

    async def _get_redis_pool(self):
        """Optimized Redis connection pool"""
        if self.redis_pool is None:
            async with self._redis_lock:
                if self.redis_pool is None:
                    try:
                        redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}" if settings.REDIS_PASSWORD else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                        self.redis_pool = redis.ConnectionPool.from_url(
                            redis_url,
                            max_connections=settings.REDIS_POOL_SIZE,
                            retry_on_timeout=True,
                            decode_responses=True,
                            socket_keepalive=True,
                            socket_keepalive_options={},
                        )
                        # Test connection
                        redis_client = redis.Redis(connection_pool=self.redis_pool)
                        await redis_client.ping()
                        await redis_client.close()
                    except Exception as e:
                        print(f"Redis connection failed: {e}")
                        self.redis_pool = None
        return self.redis_pool

    @lru_cache(maxsize=1000)
    def _generate_cache_key(self, content: str, title: str, description: str, category: str) -> str:
        """Optimized cache key generation with LRU cache"""
        cache_data = {
            "content": content.strip() if content else "",
            "title": title.strip() if title else "",
            "description": description.strip() if description else "",
            "category": category.strip() if category else ""
        }
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return f"spam:{hashlib.md5(cache_string.encode('utf-8')).hexdigest()}"

    def _check_memory_cache(self, cache_key: str) -> Optional[bool]:
        """Check in-memory cache first (fastest)"""
        if cache_key in self._memory_cache:
            result, timestamp = self._memory_cache[cache_key]
            if time.time() - timestamp < self._memory_cache_ttl:
                return result
            else:
                del self._memory_cache[cache_key]
        return None

    def _set_memory_cache(self, cache_key: str, result: bool):
        """Set in-memory cache with size limit"""
        if len(self._memory_cache) >= self._memory_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        
        self._memory_cache[cache_key] = (result, time.time())

    async def _get_from_redis_cache(self, cache_key: str) -> Optional[bool]:
        """Get from Redis cache with connection pooling"""
        try:
            pool = await self._get_redis_pool()
            if pool:
                redis_client = redis.Redis(connection_pool=pool)
                cached_result = await redis_client.get(cache_key)
                await redis_client.close()
                
                if cached_result is not None:
                    result = cached_result.lower() == "true"
                    # Also cache in memory for faster access
                    self._set_memory_cache(cache_key, result)
                    return result
        except Exception as e:
            print(f"Redis get error: {e}")
        return None

    async def _set_redis_cache(self, cache_key: str, is_spam: bool):
        """Set Redis cache with fire-and-forget approach"""
        try:
            pool = await self._get_redis_pool()
            if pool:
                redis_client = redis.Redis(connection_pool=pool)
                # Fire and forget - don't await
                asyncio.create_task(self._async_set_cache(redis_client, cache_key, is_spam))
        except Exception as e:
            print(f"Redis set error: {e}")

    async def _async_set_cache(self, redis_client, cache_key: str, is_spam: bool):
        """Async cache setter"""
        try:
            await redis_client.setex(cache_key, settings.CACHE_TTL, str(is_spam).lower())
            await redis_client.close()
        except:
            pass

    def _safe(self, x: Optional[str]) -> str:
        return str(x).strip() if x else ""

    def _truncate(self, text: str, n: int = 80) -> str:  # Giảm từ 100 xuống 80
        return " ".join(text.split()[:n])

    @lru_cache(maxsize=500)
    def _build_prompt_cached(self, title: str, content: str, desc: str, category: str, ctype: str) -> str:
        """Cached prompt building"""
        parts = []
        if ctype and ctype.endswith("Comment"):
            if title:
                parts.append(f"Post: {title}")
            if content:
                parts.append(f"Comment: {content}")
        else:
            if title:
                parts.append(f"Title: {title}")
            if content:
                parts.append(f"Content: {content}")
            if desc:
                parts.append(f"Desc: {desc}")

        text = self._truncate("\n".join(parts), 80)
        category = category or "Unknown"
        ctype = ctype or "Unknown"

        return f"""Phân loại SPAM. Chỉ trả lời: SPAM hoặc NOT_SPAM.

Category: {category}
Type: {ctype}

{text}

SPAM nếu: quảng cáo/bán hàng/sale/tuyển dụng sai ngữ cảnh; có SĐT/Zalo/link/giá; link rác/cá cược/18+; nội dung rác/vô nghĩa/lỗi font; không liên quan.
NOT_SPAM nếu: hỏi đáp, review, chia sẻ, phàn nàn, thảo luận bình thường.

Output: SPAM hoặc NOT_SPAM"""

    def _build_prompt(self, request: SpamRequest) -> str:
        return self._build_prompt_cached(
            self._safe(request.title),
            self._safe(request.content),
            self._safe(request.description),
            self._safe(request.category),
            self._safe(request.type)
        )

    def _parse(self, text: str) -> bool:
        t = (text or "").strip().upper()
        return not t.startswith("NOT_SPAM")  # Default to spam if unclear

    async def _call_llm_optimized(self, prompt: str) -> str:
        """Optimized LLM call with reduced retries"""
        headers = {
            "Authorization": f"Bearer {settings.DEEPINFRA_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Return only SPAM or NOT_SPAM."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4,  # Giảm từ 8 xuống 4
            "temperature": 0,
        }

        async with self.semaphore:
            # Chỉ retry 1 lần thay vì 3
            for i in range(2):
                try:
                    r = await self.client.post(
                        settings.DEEPINFRA_API_URL,
                        headers=headers,
                        json=payload,
                    )

                    if r.status_code in (429, 500, 502, 503, 504):
                        if i == 0:  # Chỉ sleep ở lần retry đầu
                            await asyncio.sleep(0.1 + random.random() * 0.1)
                        continue

                    r.raise_for_status()
                    data = r.json()
                    return (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                except Exception:
                    if i == 0:
                        await asyncio.sleep(0.1)

        return "NOT_SPAM"

    async def detect_spam_single(self, request: SpamRequest) -> bool:
        """Optimized single spam detection"""
        # Fast bypass for newsTopic
        if request.type == "newsTopic":
            return False
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            self._safe(request.content),
            self._safe(request.title), 
            self._safe(request.description),
            self._safe(request.category)
        )
        
        # Check memory cache first (fastest)
        cached_result = self._check_memory_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Check Redis cache
        cached_result = await self._get_from_redis_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Call LLM
        prompt = self._build_prompt(request)
        res = await self._call_llm_optimized(prompt)
        is_spam = self._parse(res)
        
        # Cache results (memory + Redis)
        self._set_memory_cache(cache_key, is_spam)
        await self._set_redis_cache(cache_key, is_spam)
        
        return is_spam

    async def detect_spam_batch(self, requests: List[SpamRequest]) -> List[bool]:
        """Optimized batch processing"""
        # Separate newsTopic and regular requests
        results = [False] * len(requests)
        regular_requests = []
        regular_indices = []
        
        for i, request in enumerate(requests):
            if request.type == "newsTopic":
                results[i] = False
            else:
                regular_requests.append(request)
                regular_indices.append(i)
        
        if not regular_requests:
            return results
        
        # Process regular requests concurrently
        tasks = [self.detect_spam_single(req) for req in regular_requests]
        regular_results = await asyncio.gather(*tasks)
        
        # Merge results
        for i, result in enumerate(regular_results):
            results[regular_indices[i]] = result
        
        return results

    async def close(self):
        await self.client.aclose()
        if self.redis_pool:
            await self.redis_pool.disconnect()


# Create optimized instance
optimized_spam_detector = OptimizedSpamDetector()