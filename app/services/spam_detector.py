import asyncio
import random
import json
import hashlib
import re
import sys
import os
from typing import Optional
import httpx
import redis.asyncio as redis

from app.config import settings
from app.models import SpamRequest

# Add parent directory to path for common modules
# Fix: Use absolute path from container's /app directory
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import custom filters
try:
    from common.filter_registry import registry
    from common.real_estate_classifier import check_real_estate_spam
    from common.phone_shopee_detector import contains_vietnam_phone_or_shopee_link
    from common.bank_spam_classifier import check_bank_spam
    from common.excluded_sites import excluded_sites_manager
    from common.cake_custom_filter import classify_row
    print("✅ Custom filters loaded successfully")
    CUSTOM_FILTERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Custom filters not available: {e}")
    print(f"   Python path: {sys.path}")
    print(f"   Current dir: {os.getcwd()}")
    print(f"   Files in current dir: {os.listdir('.')}")
    
    # Create mock functions if import fails
    class MockRegistry:
        def load_from_config(self, path): pass
        def has_filter(self, brand_id): return False
        def get_filter(self, brand_id): return lambda x: False
    
    class MockExcludedSites:
        def load_from_config(self, path): pass
        def is_excluded(self, site_id): return False
    
    registry = MockRegistry()
    excluded_sites_manager = MockExcludedSites()
    
    def check_real_estate_spam(obj, cat): return False
    def check_bank_spam(obj, cat): return False
    def contains_vietnam_phone_or_shopee_link(text): return False
    def classify_row(row): 
        print("⚠️ Using MOCK classify_row - custom filters not loaded!")
        return "NO", "UNKNOWN"
    
    print("⚠️ Using mock custom filters")
    CUSTOM_FILTERS_AVAILABLE = False


# ============================================================
# Custom keyword whitelist per index (topic_id).
# Nếu title/content/description chứa bất kỳ keyword nào trong
# danh sách thì gán thẳng is_spam = False, bỏ qua LLM.
# Để thêm index mới: thêm entry vào dict bên dưới.
# ============================================================
INDEX_KEYWORD_WHITELIST: dict[str, list[str]] = {
    "67db7841ff4aaf0805487873": [
        "Van Gaz ELLE",
        "Gaz tải VAN 3",
        "Xe gaz hoặc điện",
        "Gaz 2023 bản 16 ghế",
        "Gaz thùng mui bạt Tải 1t9",
        "Mobihome gaz Vip",
        "ae chạy xe gaz",
        "Cần bán xe GAZ 20",
        "GAZ 16 CHỖ XE THANH LÍ 2026",
        "Tải Van GAZ siêu lướt",
        "Xe Van Gaz",
        "Tải Van Gaz",
    ],
}

# ============================================================
# Brand sentiment indices - for phone/Shopee detection
# ============================================================
BRAND_SENTIMENT_INDICES = {
    "69d8865a9957472efb62d227": {"name": "Panasonic Washing Machine"},
    "69d887739957472efb62d228": {"name": "Panasonic Fridge"},
    "69d8a9849957472efb62d22a": {"name": "Panasonic Air-conditioner"},
    "69d8a8c49957472efb62d229": {"name": "Panasonic Kitchenware"},
    "69dc453fc941060a5c196195": {"name": "Sanyo Air-conditioner"},
}

# ============================================================
# Category mapping
# ============================================================
CATEGORY_MAPPING = {
    "Consumer Discretionary": "retail",
    "Consumer Staples": "fmcg",
    "Communication Services": "electronic",
    "Finance": "bank",
    "Healthcare": "hospital",
    "Digital Payment": "ewallet",
    "Real Estate": "real_estate",
    "N/A": "corp",
    "Education Services": "education",
    "Information Tech": "software_technology",
    "Industrials": "logistics",
    "Energy": "energy_fuels",
    "Automotive": "automotive",
    "Bank": "bank",
    "Corp": "corp",
    "Ecommerce": "ecommerce",
    "Education": "education",
    "Electronic": "electronic",
    "Energy Fuels": "energy_fuels",
    "Entertianment Television": "entertainment_television",
    "Ewallet": "ewallet",
    "FMCG": "fmcg",
    "FnB": "fnb",
    "Healthcare Insurance": "healthcare_insurance",
    "Home Living": "home_living",
    "Hospital": "hospital",
    "Insurance": "insurance",
    "Investment": "investment",
    "Logistic Delivery": "logistic_delivery",
    "Logistics": "logistics",
    "Retail": "retail",
    "Software Technology": "software_technology",
    "Technology Motorbike Food": "technology_motorbike_food",
    "Telecomunication Internet": "telecomunication_internet"
}


def _check_index_keyword_whitelist(index: Optional[str], *fields: Optional[str]) -> Optional[bool]:
    """
    Kiểm tra whitelist keyword theo index.
    Trả về False (not spam) nếu bất kỳ field nào chứa keyword trong whitelist.
    Trả về None nếu không match (tiếp tục xử lý bình thường).
    So sánh case-insensitive.
    """
    if not index:
        return None
    keywords = INDEX_KEYWORD_WHITELIST.get(index)
    if not keywords:
        return None
    combined = " ".join(str(f) for f in fields if f).lower()
    for kw in keywords:
        if kw.lower() in combined:
            return False  # not spam
    return None


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
        self.setup_custom_filters()
    
    def setup_custom_filters(self):
        """Setup custom preprocessing filters"""
        try:
            # Get config paths
            config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'config'
            )
            
            # Load filter registry config
            brand_filters_path = os.path.join(config_dir, 'brand_filters.json')
            if os.path.exists(brand_filters_path):
                registry.load_from_config(brand_filters_path)
                stats = registry.get_stats()
                print(f"📊 Filter Registry: {stats['total_filters']} filters, {stats['total_brands_with_filter']} brands")
            else:
                print(f"⚠️ Brand filters config not found: {brand_filters_path}")
            
            # Load excluded sites config
            excluded_sites_path = os.path.join(config_dir, 'excluded_sites.json')
            if os.path.exists(excluded_sites_path):
                excluded_sites_manager.load_from_config(excluded_sites_path)
                excluded_stats = excluded_sites_manager.get_stats()
                print(f"🚫 Excluded Sites: {excluded_stats['total_excluded_sites']} sites")
            else:
                print(f"⚠️ Excluded sites config not found: {excluded_sites_path}")
            
            print("✅ Custom filters setup completed")
        except Exception as e:
            print(f"❌ Error setting up custom filters: {e}")
    
    def apply_preprocessing_filters(self, request: SpamRequest) -> Optional[dict]:
        """
        Apply preprocessing filters before LLM.
        Returns dict with spam decision if filter matches, None otherwise.
        """
        try:
            # Extract fields
            brand_id = str(request.index or "")
            site_id = str(request.site_id or "")
            item_type = str(request.type or "")
            category = str(request.category or "")
            
            # Map category
            mapped_category = CATEGORY_MAPPING.get(category, category).lower()
            
            # Pre-filter 0: Excluded sites (highest priority)
            if site_id and excluded_sites_manager.is_excluded(site_id):
                print(f"🚫 Excluded site: {site_id}")
                return {
                    "spam": False,
                    "reason": "excluded_site",
                    "used_custom_filter": True
                }
            
            # Pre-filter 1: CAKE Custom Filter (brand-specific)
            if brand_id == "61b8715499ce4372a5d739a0":
                try:
                    row_data = {
                        "Title": self._safe(request.title),
                        "Content": self._safe(request.content),
                        "Description": self._safe(request.description)
                    }
                    is_spam_result, spam_reason = classify_row(row_data)
                    spam_bool = is_spam_result == "YES"
                    print(f"🍰 CAKE filter: spam={spam_bool} ({spam_reason})")
                    return {
                        "spam": spam_bool,
                        "reason": f"cake_custom_filter_{spam_reason.lower()}",
                        "used_custom_filter": True
                    }
                except Exception as e:
                    print(f"⚠️ CAKE filter error: {e}")
            
            # Pre-filter 2: News Topic
            if item_type == "newsTopic":
                print(f"📰 News topic detected")
                return {
                    "spam": False,
                    "reason": "news_topic",
                    "used_custom_filter": False
                }
            
            # Pre-filter 3: Phone/Shopee Detection
            if brand_id in BRAND_SENTIMENT_INDICES:
                text = f"{self._safe(request.title)}\n{self._safe(request.description)}\n{self._safe(request.content)}"
                try:
                    if contains_vietnam_phone_or_shopee_link(text):
                        print(f"📱 Phone/Shopee detected for brand {brand_id}")
                        return {
                            "spam": True,
                            "reason": "phone_shopee_detected",
                            "used_custom_filter": True
                        }
                except Exception as e:
                    print(f"⚠️ Phone/Shopee detection error: {e}")
            
            # Pre-filter 4: Custom Brand Filter (Registry)
            if brand_id and registry.has_filter(brand_id):
                try:
                    custom_filter = registry.get_filter(brand_id)
                    filter_obj = {
                        "title": self._safe(request.title),
                        "content": self._safe(request.content),
                        "description": self._safe(request.description),
                        "topic": "",  # Not available in SpamRequest
                        "site_id": site_id,
                        "type": item_type,
                        "parent_id": ""  # Not available in SpamRequest
                    }
                    is_spam_result = custom_filter(filter_obj)
                    print(f"🎯 Custom brand filter for {brand_id}: spam={is_spam_result}")
                    return {
                        "spam": is_spam_result,
                        "reason": "custom_brand_filter",
                        "used_custom_filter": True
                    }
                except Exception as e:
                    print(f"⚠️ Custom brand filter error: {e}")
            
            # Pre-filter 5: Real Estate Classifier
            if mapped_category != "real_estate":
                filter_obj = {
                    "title": self._safe(request.title),
                    "content": self._safe(request.content),
                    "description": self._safe(request.description)
                }
                try:
                    is_re_spam = check_real_estate_spam(filter_obj, mapped_category)
                    if is_re_spam:
                        print(f"🏠 Real estate spam detected in category: {mapped_category}")
                        return {
                            "spam": True,
                            "reason": "real_estate_classified",
                            "used_custom_filter": True
                        }
                except Exception as e:
                    print(f"⚠️ Real estate classifier error: {e}")
            
            # Pre-filter 6: Bank Spam Classifier
            if mapped_category == "bank":
                filter_obj = {
                    "title": self._safe(request.title),
                    "content": self._safe(request.content),
                    "description": self._safe(request.description)
                }
                try:
                    is_bank_spam = check_bank_spam(filter_obj, mapped_category)
                    if is_bank_spam:
                        print(f"🏦 Bank spam detected (non-bank content in bank category)")
                        return {
                            "spam": True,
                            "reason": "bank_spam_classified",
                            "used_custom_filter": True
                        }
                except Exception as e:
                    print(f"⚠️ Bank spam classifier error: {e}")
            
            # No preprocessing filter matched
            return None
            
        except Exception as e:
            print(f"❌ Preprocessing filters error: {e}")
            return None

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

        text = self._truncate("\n".join(parts), 100)

        category = self._safe(request.category) or "Unknown"
        ctype = self._safe(request.type) or "Unknown"

        return f"""Phân loại SPAM. Chỉ trả lời: SPAM hoặc NOT_SPAM.

Category: {category}
Type: {ctype}

{text}

SPAM nếu: quảng cáo/bán hàng/sale/tuyển dụng sai ngữ cảnh; có SĐT/Zalo/link/giá; link rác/cá cược/18+; nội dung rác/vô nghĩa/lỗi font; không liên quan.
NOT_SPAM nếu: hỏi đáp, review, chia sẻ, phàn nàn, thảo luận bình thường, tin tức, phân tích.

Luật đặc biệt:
- Real Estate + có SĐT/Zalo/link/giá cụ thể => SPAM (rao vặt)
- Real Estate + hỏi đáp/tư vấn/review => NOT_SPAM (thảo luận)
- Finance + thảo luận/phân tích/tin tức/hỏi đáp => NOT_SPAM (dù dài)
- Finance + có SĐT/link dịch vụ tài chính => SPAM
- BĐS sai category => SPAM
- Tuyển dụng sai category => SPAM
- Có từ "liên hệ", "bán", "cho thuê" + SĐT => SPAM
- Comment dài với hashtag tin tức => NOT_SPAM (thảo luận)
- Bài viết có nguồn tin (Báo, VTV, etc) => NOT_SPAM (tin tức)

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
        # --- Apply custom preprocessing filters first ---
        preprocess_result = self.apply_preprocessing_filters(request)
        if preprocess_result is not None:
            # Custom filter matched, return result
            print(f"✅ Custom filter applied: {preprocess_result['reason']}")
            return preprocess_result["spam"]
        
        # --- Index-level keyword whitelist (scale-friendly) ---
        whitelist_result = _check_index_keyword_whitelist(
            request.index,
            request.title,
            request.content,
            request.description,
        )
        if whitelist_result is not None:
            return whitelist_result

        # Special case: index 65808b57f27526950c9feb3 - custom logic
        if request.index == "65808b57f27526950c9feb3":
            content_text = self._safe(request.content) or self._safe(request.description)
            title_text = self._safe(request.title)
            
            # Kiểm tra nếu là quảng cáo tour du lịch => NOT_SPAM
            tour_keywords = [
                "tour du lịch", "khám phá", "du lịch", "hành trình", "chuyến đi",
                "điểm đến", "thăm quan", "tham quan", "trải nghiệm", "chiêm ngưỡng",
                "công viên", "di sản", "kỳ quan", "thác nước", "núi", "biển",
                "thành phố", "phố cổ", "chùa", "đền", "lăng", "cung điện"
            ]
            
            # Kiểm tra có từ khóa tour du lịch
            has_tour_keywords = any(kw in content_text.lower() for kw in tour_keywords)
            
            # Nếu là tour du lịch => NOT_SPAM
            if has_tour_keywords:
                return False
            
            # Nếu không phải tour, kiểm tra dấu hiệu rao vặt BĐS
            has_phone = bool(re.search(r'\b0\d{9}\b', content_text))
            has_zalo = "zalo" in content_text.lower()
            has_price = bool(re.search(r'\d+\s*(triệu|tỷ|đ|vnd)', content_text.lower()))
            has_contact_keywords = any(kw in content_text.lower() for kw in ["liên hệ", "bán", "cho thuê", "inbox"])
            has_bds_keywords = any(kw in title_text.lower() for kw in ["rao vặt", "bán nhà", "cho thuê", "bất động sản"])
            
            # Nếu có dấu hiệu rao vặt BĐS => SPAM, ngược lại => NOT_SPAM
            if has_phone or has_zalo or has_price or has_contact_keywords or has_bds_keywords:
                return True
            else:
                return False
        
        # Bypass: nếu type là newsTopic thì trả về False (không phải spam)
        if request.type == "newsTopic":
            return False
        
        # Pre-check: Nội dung có trích dẫn nguồn tin chính thống => NOT_SPAM
        content_text = self._safe(request.content) or self._safe(request.description)
        if content_text:
            # Kiểm tra có nguồn tin tức chính thống
            news_sources = [
                "nguồn:", "theo báo", "báo ", "vtv", "vov", "vnexpress", 
                "tuổi trẻ", "thanh niên", "dân trí", "vietnamnet", "zing news",
                "theo vtc", "theo vn", "tin từ", "trích nguồn"
            ]
            has_news_source = any(source in content_text.lower() for source in news_sources)
            
            # Kiểm tra không có dấu hiệu spam rõ ràng
            spam_indicators = ["liên hệ:", "zalo:", "sdt:", "hotline:", "inbox"]
            has_spam_indicator = any(indicator in content_text.lower() for indicator in spam_indicators)
            
            # Kiểm tra có số điện thoại (pattern: 0xxxxxxxxx)
            has_phone = bool(re.search(r'\b0\d{9}\b', content_text))
            
            # Nếu có nguồn tin chính thống và không có spam indicators => NOT_SPAM
            if has_news_source and not has_spam_indicator and not has_phone:
                return False
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # If not in cache, perform spam detection with LLM
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