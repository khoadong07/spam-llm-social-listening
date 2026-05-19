"""
Panasonic custom spam classifier — 7 rules từ spam_rule sheet (2026-05-19).

Applied when index belongs to PANASONIC_INDICES.

Returns:
  - dict  {"is_spam": bool, "reason": str, "matched_rules": list[str]}
           when a rule fires.
  - None  when no rule matches → caller falls through to general spam processing.
"""

import re
from typing import Optional


# ── INDEX SET ────────────────────────────────────────────────────────────────
PANASONIC_INDICES = {
    "69d8865a9957472efb62d227",  # Panasonic Washing Machine
    "69d887739957472efb62d228",  # Panasonic Fridge
    "69d8a9849957472efb62d22a",  # Panasonic Air-conditioner
    "69d8a8c49957472efb62d229",  # Panasonic Kitchenware
}


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
_PANASONIC_BRAND = ["panasonic", "pana"]

_BDS_KW = [
    "bán nhà", "bán đất", "bán căn hộ", "bán chung cư", "bán gấp nhà",
    "cho thuê nhà", "cho thuê căn hộ", "cho thuê mặt bằng",
    "căn hộ", "chung cư", "nhà phố", "đất nền", "đất thổ cư",
    "mặt tiền", "hẻm", "ngõ", "phòng ngủ", "wc", "toilet", "phòng tắm",
    "nội thất đầy đủ", "sổ hồng", "sổ đỏ", "shr",
]
_BDS_RE = re.compile(
    r"ngang\s*\d|dài\s*\d|diện tích\s*\d|\d+\s*m2|\d+\s*wc|\d+\s*pn"
    r"|\d+\s*phòng ngủ|\d+\s*phòng tắm",
    re.IGNORECASE,
)

_THANHLY_KW = [
    "thanh lý", "bán lại", "cần bán", "bán gấp", "cần pass", "pass lại",
    "sell", "rao bán", "cần ra đi", "xả kho",
]
_USED_KW = [
    "đã qua sử dụng", "second hand", "hàng cũ", "hàng bãi", "nội địa nhật",
    "nội địa", "zin nguyên", "zin", "mới đẹp", "còn tốt", "đã tét",
    "đã dùng", "qua sử dụng",
]
_PRICE_RE = re.compile(
    r"\b\d{1,3}tr\b|\b\d{1,3}\s*triệu\b|\b\d{1,3}k\b"
    r"|\d{1,3}[.,]\d{3}[.,]\d{3}|\d{1,3}\.\d{3}đ"
    r"|giá chỉ|giá còn|giá rẻ",
    re.IGNORECASE,
)
_SELL_CONTACT_KW = ["inbox", "zalo", "liên hệ", "alo", "gọi", "nhắn tin", "ib"]

_NHAT_BAI_RE = re.compile(
    r"nhật\s*bãi|bãi\s*nhật|hàng\s*nhật\s*bãi|đồ\s*nhật\s*bãi"
    r"|nhat\s*bai|bai\s*nhat|hang\s*nhat\s*bai",
    re.IGNORECASE,
)

_REPAIR_KW = [
    "dịch vụ sửa", "chuyên sửa", "thợ sửa", "sửa chữa", "sửa điều hòa",
    "sửa máy lạnh", "sửa tủ lạnh", "sửa máy giặt", "bảo dưỡng",
    "vệ sinh máy lạnh", "vệ sinh điều hòa", "lắp đặt điều hòa",
    "thợ lắp", "lắp máy lạnh", "lắp ráp điều hòa",
]
_REPAIR_CONTACT_RE = re.compile(
    r"0[35789]\d{8}|\+84[35789]\d{8}|gọi ngay|liên hệ ngay|hotline",
    re.IGNORECASE,
)

_PHONE_RE = re.compile(
    r"0[35789]\d{8}|\+84[35789]\d{8}|0\d{2,3}[.\-]\d{3,4}[.\-]\d{3,4}",
    re.IGNORECASE,
)

_DIEN_MAY_RE = re.compile(
    r"điện máy xanh|điện máy chợ lớn|điện máy nguyễn kim|mediamart|media mart"
    r"|\bpico\b|nguyễn kim|fpt shop|vinhpro|điện máy thiên hòa"
    r"|điện máy hoàng hải|điện máy phượng vàng|điện máy mạnh cường"
    r"|siêu thị điện máy",
    re.IGNORECASE,
)

_MINIGAME_RE = re.compile(
    r"minigame|mini.?game"
    r"|bình luận để (nhận|trúng|tham gia)"
    r"|comment để (nhận|trúng)"
    r"|tag\s+\w+\s+để nhận"
    r"|like\s+(và|&|share)"
    r"|vòng quay (may mắn|quà)"
    r"|trả lời (câu hỏi )?để nhận",
    re.IGNORECASE,
)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _has_pana(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _PANASONIC_BRAND)


def _has_bds(text: str) -> bool:
    return any(k in text for k in _BDS_KW) or bool(_BDS_RE.search(text))


# ── MAIN CLASSIFIER ───────────────────────────────────────────────────────────
def classify_panasonic_spam(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
    is_post: bool = True,
    site_name: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Optional[dict]:
    """
    Apply 7 Panasonic spam rules to a single item.

    Parameters
    ----------
    title, content, description : text fields
    is_post      : True if Topic/Post, False if Comment
    site_name    : page/site name (used for R3 and R6)
    content_type : type field from SpamRequest (unused, reserved for future)

    Returns
    -------
    dict  when a rule fires → {"is_spam": bool, "reason": str, "matched_rules": list[str]}
    None  when no rule matches → caller continues to general spam processing
    """
    title       = (title or "").strip()
    content     = (content or "").strip()
    description = (description or "").strip()
    site        = (site_name or "").strip().lower()

    all_text = (title + " " + content + " " + description).lower()

    # ── R1: BĐS + thiết bị Panasonic ─────────────────────────────────────────
    if _has_bds(all_text) and _has_pana(all_text):
        return {
            "is_spam": True,
            "reason": "panasonic_R1_bds_product",
            "matched_rules": ["R1: Bất động sản + thiết bị Panasonic"],
        }

    # ── R2: Thanh lý / rao bán sản phẩm Panasonic ───────────────────────────
    is_thanhly       = any(k in all_text for k in _THANHLY_KW)
    is_used          = any(k in all_text for k in _USED_KW)
    has_price        = bool(_PRICE_RE.search(all_text))
    has_sell_contact = any(k in all_text for k in _SELL_CONTACT_KW)

    if _has_pana(all_text) and (is_thanhly or is_used) and (has_price or has_sell_contact):
        return {
            "is_spam": True,
            "reason": "panasonic_R2_thanhly_banhang",
            "matched_rules": ["R2: Thanh lý / rao bán sản phẩm Panasonic"],
        }

    # ── R3: Nhật bãi / Bãi Nhật ─────────────────────────────────────────────
    if _NHAT_BAI_RE.search(site) or _NHAT_BAI_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "panasonic_R3_nhat_bai",
            "matched_rules": ["R3: Rao bán sản phẩm Nhật bãi / Bãi Nhật"],
        }

    # ── R4: Dịch vụ sửa chữa / lắp ráp bên thứ 3 ───────────────────────────
    if any(k in all_text for k in _REPAIR_KW) and _REPAIR_CONTACT_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "panasonic_R4_repair_service",
            "matched_rules": ["R4: Dịch vụ sửa chữa / lắp ráp bên thứ 3"],
        }

    # ── R5: Số điện thoại trong Post (Comment được bỏ qua) ──────────────────
    if is_post and _PHONE_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "panasonic_R5_phone_in_post",
            "matched_rules": ["R5: Bài đăng (Post) có số điện thoại"],
        }

    # ── R6: Kênh điện máy + Post (Comment được alert bình thường) ───────────
    if is_post and site and _DIEN_MAY_RE.search(site):
        return {
            "is_spam": True,
            "reason": "panasonic_R6_dien_may_channel",
            "matched_rules": ["R6: Bài đăng từ kênh điện máy"],
        }

    # ── R7: Minigame — cả Post lẫn Comment ──────────────────────────────────
    if _MINIGAME_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "panasonic_R7_minigame",
            "matched_rules": ["R7: Nội dung liên quan Minigame"],
        }

    # No rule matched → fall through to general spam processing
    return None
