import asyncio
import random
import json
import hashlib
import re
from typing import Optional, Dict, Any, List
import httpx
import redis.asyncio as redis
from functools import lru_cache
import time

from app.config import settings
from app.models import SpamRequest
from app.services.spam_detector import INDEX_KEYWORD_WHITELIST, _check_index_keyword_whitelist

try:
    from common.fwd_custom import classify_fwd_spam, FWD_INDICES
    from common.ghn_custom import classify_ghn_custom, GHN_INDICES
    from common.bidv_custom import classify_bidv_spam, BIDV_INDICES
    from common.panasonic_custom import classify_panasonic_spam, PANASONIC_INDICES
except ImportError:
    def classify_fwd_spam(title, content, description):
        return {"is_spam": False, "reason": "fwd_mock"}
    FWD_INDICES: set = set()

    def classify_ghn_custom(title, content, description, site_name=None):
        return {"is_spam": False, "reason": "ghn_mock"}
    GHN_INDICES: set = set()

    def classify_bidv_spam(title, content, description, is_post=True, channel=None, content_type=None):
        return None
    BIDV_INDICES: set = set()

    def classify_panasonic_spam(title, content, description, is_post=True, site_name=None, content_type=None):
        return None
    PANASONIC_INDICES: set = set()


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
    def _build_prompt_cached(self, title: str, content: str, desc: str, category: str, ctype: str, version: int = 2) -> str:
        """Cached prompt building - version param để force clear cache khi update"""
        parts = []
        if ctype and ctype.endswith("Comment"):
            if title:
                parts.append(f"Post: {title}")
            if content:
                parts.append(f"Comment: {content}")
            elif desc:  # Nếu không có content thì dùng description
                parts.append(f"Comment: {desc}")
        else:
            if title:
                parts.append(f"Title: {title}")
            # Ưu tiên content, nếu không có thì dùng description
            if content:
                parts.append(f"Content: {content}")
                if desc and desc != content:  # Thêm desc nếu khác content
                    parts.append(f"Desc: {desc}")
            elif desc:  # Nếu chỉ có description
                parts.append(f"Content: {desc}")

        text = self._truncate("\n".join(parts), 80)
        category = category or "Unknown"
        ctype = ctype or "Unknown"

        return f"""Phân loại SPAM. Chỉ trả lời: SPAM hoặc NOT_SPAM.

Category: {category}
Type: {ctype}

{text}

SPAM nếu: quảng cáo/bán hàng/sale/tuyển dụng sai ngữ cảnh; có SĐT/Zalo/link/giá; link rác/cá cược/18+; nội dung rác/vô nghĩa/lỗi font; không liên quan.
NOT_SPAM nếu: hỏi đáp, review, chia sẻ, phàn nàn, thảo luận bình thường, tin tức, phân tích, bình luận xã hội.

Luật đặc biệt:
- Real Estate + có SĐT/Zalo/link/giá cụ thể => SPAM (rao vặt)
- Real Estate + hỏi đáp/tư vấn/review => NOT_SPAM (thảo luận)
- Finance + thảo luận/phân tích/tin tức/hỏi đáp => NOT_SPAM (dù dài)
- Finance + có SĐT/link dịch vụ tài chính => SPAM
- BĐS sai category => SPAM
- Tuyển dụng sai category => SPAM
- Có từ "liên hệ", "bán", "cho thuê" + SĐT => SPAM (phải có SĐT đi kèm)
- Comment/bài viết dài với hashtag tin tức (#tintuc, #tiktoknews, #news, v.v.) + không có SĐT/link/giá => NOT_SPAM (thảo luận/tin tức mạng xã hội)
- Bài viết có nguồn tin (Báo, VTV, etc) => NOT_SPAM (tin tức)
- Bài viết thảo luận chính sách/sản phẩm/dịch vụ công cộng (xăng dầu, điện, nước, y tế...) + không có SĐT/Zalo => NOT_SPAM (thảo luận công cộng)
- Buzz/post mạng xã hội về thương hiệu lớn (Petrolimex, EVN, VNPT, Vingroup...) dạng chia sẻ/nhận xét + không rao bán => NOT_SPAM

Output: SPAM hoặc NOT_SPAM"""

    def _build_prompt(self, request: SpamRequest) -> str:
        return self._build_prompt_cached(
            self._safe(request.title),
            self._safe(request.content),
            self._safe(request.description),
            self._safe(request.category),
            self._safe(request.type),
            version=3  # Tăng version để clear cache
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
        # --- Index-level keyword whitelist (scale-friendly) ---
        whitelist_result = _check_index_keyword_whitelist(
            request.index,
            request.title,
            request.content,
            request.description,
        )
        if whitelist_result is not None:
            return whitelist_result

        brand_id = str(request.index or "")

        # FWD Custom Filter
        if brand_id in FWD_INDICES:
            try:
                fwd_result = classify_fwd_spam(
                    request.title,
                    request.content,
                    request.description,
                )
                print(f"🔵 FWD filter (index: {brand_id}): spam={fwd_result['is_spam']}, reason={fwd_result['reason']}")
                return fwd_result["is_spam"]
            except Exception as e:
                print(f"⚠️ FWD filter error: {e}")

        # GHN Custom Filter
        if brand_id in GHN_INDICES:
            try:
                ghn_result = classify_ghn_custom(
                    title=request.title,
                    content=request.content,
                    description=request.description,
                    site_name=request.site_name or None,
                )
                matched = ghn_result.get("matched_rules", [])
                print(
                    f"🟡 GHN filter | index={brand_id} | "
                    f"spam={ghn_result['is_spam']} | "
                    f"reason={ghn_result['reason']} | "
                    f"matched={matched}"
                )
                return ghn_result["is_spam"]
            except Exception as e:
                print(f"⚠️ GHN filter error: {e}")

        # BIDV Custom Filter (banking project topics)
        if brand_id in BIDV_INDICES:
            try:
                _is_post = not request.type.endswith("Comment")
                bidv_result = classify_bidv_spam(
                    title=request.title,
                    content=request.content,
                    description=request.description,
                    is_post=_is_post,
                    channel=None,
                    content_type=request.type,
                )
                if bidv_result is not None:
                    matched = bidv_result.get("matched_rules", [])
                    print(
                        f"🏦 BIDV filter | index={brand_id} | "
                        f"spam={bidv_result['is_spam']} | "
                        f"reason={bidv_result['reason']} | "
                        f"matched={matched}"
                    )
                    return bidv_result["is_spam"]
                # None → no rule matched, fall through to general spam processing
            except Exception as e:
                print(f"⚠️ BIDV filter error: {e}")

        # Panasonic Custom Filter
        if brand_id in PANASONIC_INDICES:
            try:
                _is_post = not request.type.endswith("Comment")
                pana_result = classify_panasonic_spam(
                    title=request.title,
                    content=request.content,
                    description=request.description,
                    is_post=_is_post,
                    site_name=request.site_name or None,
                    content_type=request.type,
                )
                if pana_result is not None:
                    matched = pana_result.get("matched_rules", [])
                    print(
                        f"📺 Panasonic filter | index={brand_id} | "
                        f"spam={pana_result['is_spam']} | "
                        f"reason={pana_result['reason']} | "
                        f"matched={matched}"
                    )
                    return pana_result["is_spam"]
                # None → no rule matched, fall through to general spam processing
            except Exception as e:
                print(f"⚠️ Panasonic filter error: {e}")

        # Fast bypass for newsTopic
        if request.type == "newsTopic":
            return False

        # Profile update: title + content đều rỗng VÀ description có dạng profile update => SPAM
        _PROFILE_UPDATE_PATTERNS = [
            r"đã cập nhật ảnh đại diện",
            r"đã thay đổi ảnh đại diện",
            r"đã cập nhật ảnh bìa",
            r"đã thay đổi ảnh bìa",
            r"updated (?:their |his |her )?profile picture",
            r"updated (?:their |his |her )?cover photo",
            r"changed (?:their |his |her )?profile picture",
            r"changed (?:their |his |her )?cover photo",
        ]
        _pf_title = self._safe(request.title)
        _pf_content = self._safe(request.content)
        _pf_desc = self._safe(request.description)
        if not _pf_title and not _pf_content and _pf_desc:
            for _pattern in _PROFILE_UPDATE_PATTERNS:
                if re.search(_pattern, _pf_desc, re.IGNORECASE):
                    print(f"🖼️ Profile update detected (title & content empty, desc matches) => SPAM")
                    return True
        
        # Pre-check: Nội dung có trích dẫn nguồn tin chính thống => NOT_SPAM
        content_text = self._safe(request.content) or self._safe(request.description)
        if content_text:
            content_lower = content_text.lower()

            # Kiểm tra có nguồn tin tức chính thống
            news_sources = [
                "nguồn:", "theo báo", "báo ", "vtv", "vov", "vnexpress",
                "tuổi trẻ", "thanh niên", "dân trí", "vietnamnet", "zing news",
                "theo vtc", "theo vn", "tin từ", "trích nguồn"
            ]
            has_news_source = any(source in content_lower for source in news_sources)

            # Kiểm tra hashtag tin tức phổ biến trên mạng xã hội
            news_hashtags = [
                "#tintuc", "#tiktoknews", "#news", "#xangdau", "#petrolimex",
                "#fyp", "#fyb", "#foryou", "#trending", "#viral",
                "#chiase", "#thongtin", "#sukien"
            ]
            has_news_hashtag = any(tag in content_lower for tag in news_hashtags)

            # Kiểm tra không có dấu hiệu spam rõ ràng
            spam_indicators = ["liên hệ:", "zalo:", "sdt:", "hotline:", "inbox"]
            has_spam_indicator = any(indicator in content_lower for indicator in spam_indicators)

            # Kiểm tra có số điện thoại (pattern: 0xxxxxxxxx)
            has_phone = bool(re.search(r'\b0\d{9}\b', content_text))

            # Nếu có nguồn tin chính thống và không có spam indicators => NOT_SPAM
            if has_news_source and not has_spam_indicator and not has_phone:
                return False

            # Buzz mạng xã hội: có hashtag tin tức, không có spam indicators, không có SĐT => NOT_SPAM
            if has_news_hashtag and not has_spam_indicator and not has_phone:
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