import asyncio
import random
import json
import hashlib
from typing import Optional
import httpx
import redis.asyncio as redis

from app.config import settings
from app.models import SpamRequest


class SpamDetector:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_connections=settings.MAX_CONCURRENT_REQUESTS * 2,
                max_keepalive_connections=settings.MAX_CONCURRENT_REQUESTS,
            ),
        )
        self.redis_client = None

    async def _get_redis_client(self):
        """Lazy initialization of Redis client"""
        if self.redis_client is None:
            try:
                redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}" if settings.REDIS_PASSWORD else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None
        return self.redis_client

    def _generate_cache_key(self, request: SpamRequest) -> str:
        """Generate cache key from request content, title, description, category"""
        cache_data = {
            "content": self._safe(request.content),
            "title": self._safe(request.title),
            "description": self._safe(request.description),
            "category": self._safe(request.category)
        }
        # Create hash from sorted JSON to ensure consistent keys
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return f"spam_cache:{hashlib.md5(cache_string.encode('utf-8')).hexdigest()}"

    async def _get_from_cache(self, cache_key: str) -> Optional[bool]:
        """Get spam detection result from cache"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                cached_result = await redis_client.get(cache_key)
                if cached_result is not None:
                    return cached_result.lower() == "true"
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    async def _set_cache(self, cache_key: str, is_spam: bool):
        """Set spam detection result to cache with TTL"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                await redis_client.setex(cache_key, settings.CACHE_TTL, str(is_spam).lower())
        except Exception as e:
            print(f"Cache set error: {e}")

    def _safe(self, x: Optional[str]) -> str:
        return str(x).strip() if x else ""

    def _truncate(self, text: str, n: int = 100) -> str:
        return " ".join(text.split()[:n])

    def _build_prompt(self, request: SpamRequest) -> str:
        title = self._safe(request.title)
        content = self._safe(request.content)
        desc = self._safe(request.description)

        parts = []
        if request.type and request.type.endswith("Comment"):
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

        text = self._truncate("\n".join(parts), 100)

        category = self._safe(request.category) or "Unknown"
        ctype = self._safe(request.type) or "Unknown"

        return f"""Phân loại SPAM. Chỉ trả lời: SPAM hoặc NOT_SPAM.

Category: {category}
Type: {ctype}

{text}

SPAM nếu: quảng cáo/bán hàng/sale/tuyển dụng sai ngữ cảnh; có SĐT/Zalo/link/giá; link rác/cá cược/18+; nội dung rác/vô nghĩa/lỗi font; không liên quan.
NOT_SPAM nếu: hỏi đáp, review, chia sẻ, phàn nàn, thảo luận bình thường.

Luật:
- Real Estate: tin BĐS đúng ngữ cảnh => NOT_SPAM
- Finance/Bank: hỏi/chia sẻ về vay, nợ, thẻ => NOT_SPAM
- BĐS sai category => SPAM
- Tuyển dụng sai category => SPAM

Output: SPAM hoặc NOT_SPAM"""

    def _parse(self, text: str) -> bool:
        t = (text or "").strip().upper()
        if t.startswith("NOT_SPAM"):
            return False
        if t.startswith("SPAM"):
            return True
        return False

    async def _call_llm(self, prompt: str) -> str:
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
            "max_tokens": 8,
            "temperature": 0,
        }

        async with self.semaphore:
            for i in range(3):
                try:
                    r = await self.client.post(
                        settings.DEEPINFRA_API_URL,
                        headers=headers,
                        json=payload,
                    )

                    if r.status_code in (429, 500, 502, 503, 504):
                        await asyncio.sleep((2**i) + random.random())
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
                    await asyncio.sleep((2**i) + random.random())

        return "NOT_SPAM"

    async def detect_spam(self, request: SpamRequest) -> bool:
        # Bypass: nếu type là newsTopic thì trả về False (không phải spam)
        if request.type == "newsTopic":
            return False
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # If not in cache, perform spam detection
        prompt = self._build_prompt(request)
        res = await self._call_llm(prompt)
        is_spam = self._parse(res)
        
        # Cache the result
        await self._set_cache(cache_key, is_spam)
        
        return is_spam

    async def close(self):
        await self.client.aclose()
        if self.redis_client:
            await self.redis_client.aclose()


spam_detector = SpamDetector()