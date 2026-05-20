"""
SHB Bank custom spam classifier — 7 rules.

Applied when index belongs to SHB_INDICES.
SHB_MAINBRAND_INDICES: các index là Mainbrand SHB → giữ data bóng đá (R6 không áp dụng).

Returns:
  - dict  {"is_spam": bool, "reason": str, "matched_rules": list[str]}
           when a rule fires.
  - None  when no rule matches → caller falls through to general spam processing.
"""

import re
from typing import Optional


# ── INDEX SETS ───────────────────────────────────────────────────────────────
SHB_INDICES = {
    "5683bd53f9876f7e0db58a7b",  # SHB (Mainbrand)
    "6664210e1312aa2f3ba78f7d",  # ACB Bank - SHB
    "6666bd68d02b8d70a3d052a3",  # MBBank - SHB
    "6666bd73d02b8d70a3d052a4",  # MSB - SHB
    "6666bd9cd02b8d70a3d052a6",  # Sacombank - SHB
    "6666becbd02b8d70a3d052a9",  # Techcombank - SHB
    "6666bbd2d02b8d70a3d0529a",  # VPBank - SHB
    "6666bc02d02b8d70a3d0529c",  # Vietcombank - SHB
    "68637e3b398f863c83be8d65",  # TPBank - SHB
    "68637e50398f863c83be8d66",  # VIB - SHB
    "68637e68398f863c83be8d67",  # BIDV - SHB
    "68637e95398f863c83be8d68",  # Vietinbank - SHB
}

# Mainbrand SHB → giữ data bóng đá (SHB tài trợ CLB bóng đá SHB Đà Nẵng)
SHB_MAINBRAND_INDICES = {
    "5683bd53f9876f7e0db58a7b",  # SHB
}


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
_SHB_KEYWORDS = [
    "shb", "ngân hàng shb", "saigon hanoi bank",
    "ngân hàng sài gòn hà nội", "ngân hàng sai gon ha noi",
]

_FINANCE_CONTEXT_KW = [
    "lãi suất", "tiết kiệm", "vay vốn", "vay tiền", "tín dụng",
    "thẻ tín dụng", "thẻ atm", "tài khoản ngân hàng", "mở tài khoản",
    "chuyển khoản", "thanh toán", "ngân hàng số", "mobile banking",
    "internet banking", "ebanking", "stk ngân hàng", "số tài khoản ngân hàng",
    "shb", "ngân hàng",
]

# Finance context dành riêng cho R8c — không gồm tên ngân hàng để tránh vòng lặp
_FINANCE_CONTEXT_R8C_KW = [
    "lãi suất", "tiết kiệm", "vay vốn", "vay tiền", "tín dụng",
    "thẻ tín dụng", "thẻ atm", "tài khoản ngân hàng", "mở tài khoản",
    "chuyển khoản", "ngân hàng số", "mobile banking",
    "internet banking", "ebanking",
]

_BDS_KW = [
    "bất động sản", "bán nhà", "bán đất", "cho thuê nhà", "cho thuê căn hộ",
    "cho thuê mặt bằng", "căn hộ", "chung cư", "thổ cư", "nhà mặt tiền",
    "nhà phố", "đất nền", "nhà giá rẻ", "sổ pháp lý", "sổ hồng", "sổ đỏ",
    "đông dân cư", "khu vực kinh doanh", "mặt bằng kinh doanh",
    "phòng ngủ", "wc", "toilet", "nội thất đầy đủ", "hẻm", "shr",
]
_BDS_RE = re.compile(
    r"ngang\s*\d|dài\s*\d|diện tích\s*\d|\d+\s*m2|\d+\s*wc|\d+\s*pn"
    r"|\d+\s*phòng ngủ|giá bán\s*\d|giá chỉ\s*\d",
    re.IGNORECASE,
)

_DONATE_KW = [
    "lòng hảo tâm", "ủng hộ qua stk", "ủng hộ qua số tài khoản",
    "mong anh chị giúp đỡ", "a di đà phật", "nam mô",
    "bệnh hiểm nghèo", "hoàn cảnh khó khăn", "ủng hộ kênh",
    "quyên góp", "donate", "từ thiện", "thiện nguyện",
    "cầu xin", "xin giúp đỡ", "xin ủng hộ",
]
_ACCOUNT_RE = re.compile(r"\d{6,}")

_SPAM_LINK_RE = re.compile(
    r"bit\.ly/|tinyurl\.com/|t\.co/|rb\.gy/|shorturl\.at/"
    r"|cutt\.ly/|ow\.ly/|goo\.gl/|tiny\.cc/",
    re.IGNORECASE,
)

_THANHLY_KW = [
    "thanh lý", "pass lại", "pass đồ", "nhượng lại", "cần pass",
    "dọn nhà", "xả kho cá nhân", "xả kho", "cần bán gấp",
    "fix giá", "giá fix", "không kì kèo",
]
_THANHLY_PRODUCT_KW = [
    "tủ lạnh", "máy giặt", "điều hòa", "máy lạnh", "nồi cơm",
    "máy xay", "lò vi sóng", "bếp từ", "bình nóng lạnh",
    "điện thoại", "laptop", "máy tính", "iphone", "samsung", "ipad",
    "tai nghe", "airpods", "đồng hồ thông minh",
    "quần áo", "giày dép", "túi xách", "ví da", "đồng hồ",
    "áo thun", "quần jean", "váy đầm",
]

_SPORTS_RE = re.compile(
    r"\b(bóng đá|trận đấu|tỷ số|ghi bàn|penalty|phạt đền"
    r"|hiệp [12]|ngoại hạng|champions league|world cup|v.league"
    r"|man utd|real madrid|barcelona|liverpool|chelsea|arsenal"
    r"|cầu thủ|\bhlv\b|trọng tài|bàn thắng|hat.trick"
    r"|ronaldo|messi|neymar)\b",
    re.IGNORECASE,
)

_GAME_RE = re.compile(
    r"livestream\s+game|live\s*stream\s+game|review\s+game"
    r"|tóm tắt\s+game|gameplay|\bchơi game\b|\bgaming\b"
    r"|\bleo rank\b|liên quân|liên minh huyền thoại"
    r"|\bpubg\b|\bfree fire\b|\bvalorant\b|\bminecraft\b"
    r"|\bgenshin\b|mobile legend|\bmlbb\b",
    re.IGNORECASE,
)

_WEDDING_KW = [
    "đám cưới", "thiệp cưới", "lễ cưới", "hôn lễ", "vu quy",
    "tân hôn", "wedding", "đính hôn",
]
_TANGIADM_KW = ["tân gia", "khai trương", "mừng nhà mới"]
_STORY_REVIEW_KW = [
    "review truyện", "tóm tắt truyện", "truyện ma", "truyện ngôn tình",
    "review phim", "tóm tắt phim", "spoiler",
]
_SELLING_KW = [
    "inbox", "order", "ship", "giao hàng toàn quốc",
    "liên hệ để mua", "đặt hàng", "còn hàng",
]


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _has_shb(text: str) -> bool:
    return any(kw in text for kw in _SHB_KEYWORDS)


def _has_finance_context(text: str) -> bool:
    return any(kw in text for kw in _FINANCE_CONTEXT_KW)


def _has_bds(text: str) -> bool:
    return any(k in text for k in _BDS_KW) or bool(_BDS_RE.search(text))


# ── MAIN CLASSIFIER ───────────────────────────────────────────────────────────
def classify_shb_spam(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
    is_post: bool = True,
    site_name: Optional[str] = None,
    content_type: Optional[str] = None,
    index: Optional[str] = None,
) -> Optional[dict]:
    """
    Apply 7 SHB spam rules to a single item.

    Returns
    -------
    dict  when a rule fires → {"is_spam": bool, "reason": str, "matched_rules": list[str]}
    None  when no rule matches → caller continues to general spam processing
    """
    title       = (title or "").strip()
    content     = (content or "").strip()
    description = (description or "").strip()

    all_text = (title + " " + content + " " + description).lower()
    is_mainbrand = (index or "") in SHB_MAINBRAND_INDICES

    # ── R2: BĐS + tên ngân hàng SHB ─────────────────────────────────────────
    if _has_bds(all_text) and _has_shb(all_text):
        return {
            "is_spam": True,
            "reason": "shb_R2_bds_bank_name",
            "matched_rules": ["R2: Bất động sản + tên ngân hàng SHB"],
        }

    # ── R3: Donate / từ thiện có STK ─────────────────────────────────────────
    if any(k in all_text for k in _DONATE_KW) \
            and (bool(_ACCOUNT_RE.search(all_text)) or _has_shb(all_text)):
        return {
            "is_spam": True,
            "reason": "shb_R3_donate_stk",
            "matched_rules": ["R3: Kêu gọi donate / từ thiện có STK"],
        }

    # ── R4: Link rác / clickbait ─────────────────────────────────────────────
    if _SPAM_LINK_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "shb_R4_spam_link",
            "matched_rules": ["R4: Link rác / clickbait (short URL)"],
        }

    # ── R5: Rao vặt / thanh lý đồ cá nhân ───────────────────────────────────
    if any(k in all_text for k in _THANHLY_KW) \
            and any(k in all_text for k in _THANHLY_PRODUCT_KW):
        return {
            "is_spam": True,
            "reason": "shb_R5_thanhly_raovat",
            "matched_rules": ["R5: Rao vặt / thanh lý đồ cá nhân"],
        }

    # ── R6: Thể thao / bóng đá không có ngữ cảnh tài chính ─────────────────
    # Ngoại lệ: Mainbrand SHB giữ data bóng đá
    if not is_mainbrand:
        if _SPORTS_RE.search(all_text) and not _has_finance_context(all_text):
            return {
                "is_spam": True,
                "reason": "shb_R6_sports_no_finance",
                "matched_rules": ["R6: Nội dung thể thao không liên quan tài chính"],
            }

    # ── R7: Game không do ngân hàng tổ chức ─────────────────────────────────
    if _GAME_RE.search(all_text) and not _has_shb(all_text):
        return {
            "is_spam": True,
            "reason": "shb_R7_game",
            "matched_rules": ["R7: Nội dung game không liên quan ngân hàng"],
        }

    # ── R8a: Thiệp cưới / tân gia ────────────────────────────────────────────
    if any(k in all_text for k in _WEDDING_KW + _TANGIADM_KW):
        return {
            "is_spam": True,
            "reason": "shb_R8a_wedding_tangiadm",
            "matched_rules": ["R8a: Thiệp cưới / tân gia"],
        }

    # ── R8b: Review truyện / phim không liên quan ────────────────────────────
    if any(k in all_text for k in _STORY_REVIEW_KW):
        return {
            "is_spam": True,
            "reason": "shb_R8b_story_review",
            "matched_rules": ["R8b: Review truyện / phim không liên quan"],
        }

    # ── R8c: Bán hàng + STK ngân hàng, không liên quan tài chính ─────────────
    if any(k in all_text for k in _SELLING_KW) \
            and _has_shb(all_text) \
            and not any(k in all_text for k in _FINANCE_CONTEXT_R8C_KW):
        return {
            "is_spam": True,
            "reason": "shb_R8c_selling_stk",
            "matched_rules": ["R8c: Bán hàng + STK SHB không liên quan tài chính"],
        }

    return None
