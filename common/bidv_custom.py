"""
BIDV custom spam classifier — ported from SKILL_loc_spam_BIDV.md (v1.4, 16 rules).

Applied when index belongs to BIDV_INDICES (banking project topics).

Returns:
  - dict  {"is_spam": bool, "reason": str, "matched_rules": list[str]}
           when a rule fires (either direction).
  - None  when no rule matches → caller falls through to general spam processing.
"""

import re
from typing import Optional


# ── INDEX SET ────────────────────────────────────────────────────────────────
BIDV_INDICES = {
    "5551cc314201bdbf1832ac98",  # BIDV
    "6379f2834070c0601e160076",  # Vietcombank
    "6379f32a4070c0601e160077",  # Vietinbank
    "6379f4a24070c0601e160078",  # Techcombank
    "6379f57c4070c0601e160079",  # MBBank
    "5f44e6de059c4136b924237b",  # ACB Bank
    "63f5da94f25ec30eba7b9e97",  # VPBank
    "63f5da34f25ec30eba7b9e94",  # Agribank
    "691ac7021749fd5fd31b547f",  # VPBank K-Star Spark in Vietnam
    "691ac7391749fd5fd31b5480",  # VIB - Siêu Lợi Suất
    "691ac78c1749fd5fd31b5481",  # ACB - Loa Tinh Tinh
    "691ac7e61749fd5fd31b5482",  # Techcombank - Vượt trội hơn mỗi ngày
    "691ac81c1749fd5fd31b5483",  # MSB - Cùng vươn tầm
    "691ac8651749fd5fd31b5484",  # OCB - Về nhà là có tết
    "5788c33ba761e83c39fb971c",  # TPBank
    "580ed5a403746f696a80a2c3",  # VIB
    "56fcadd282ea19d067e5dc93",  # MSB
    "63f5db8df25ec30eba7b9e9c",  # OCB
}


# ── BIDV KEYWORD LIST ─────────────────────────────────────────────────────────
_BIDV_KEYWORDS = [
    "bidv",
    "bid",
    "ngân hàng đầu tư và phát triển việt nam",
    "ngân hàng tmcp đầu tư và phát triển việt nam",
    "ngân hàng tmcp đầu tư phát triển",
    "bsc",
    "bảo hiểm bic",
    "bidvtv",
    "bidvnews",
    "smartbanking",
    "ngân hàng đt & pt việt nam",
    "bank for investment and development of vietnam",
    "trần bắc hà",
    "bank hoa mai",
    "bidv metlife",
    "bidvmetlife",
]


def _has_bidv(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _BIDV_KEYWORDS)


def _desc_has_bidv_stk(desc: str) -> bool:
    """BIDV in description paired with a real account number (6+ digits), ignoring hashtags/tickers."""
    if not desc:
        return False
    d_clean = re.sub(r"#\w+", "", desc.lower())
    if not any(kw in d_clean for kw in ["bidv", "ngân hàng đầu tư", "smartbanking"]):
        return False
    return bool(re.search(r"bidv.{0,30}\d{6,}|\d{6,}.{0,30}bidv", d_clean))


# ── RULE CONSTANTS ────────────────────────────────────────────────────────────
_DV_KW = [
    "cho thuê", "bán nhà", "bán đất", "mặt bằng", "căn hộ", "bất động sản",
    "thuê nhà", "thuê mặt", "phòng trọ",
    "làm tóc", "nail", "spa", "thẩm mỹ", "salon", "hair", "massage",
    "quán ăn", "nhà hàng", "quán cafe", "cafe", "dịch vụ",
    "thời trang", "#thoitrang", "áo sơ mi", "áo thun", "quần",
    "ăn trưa", "ăn tối", "ăn sáng",
    "peel", "mỹ phẩm", "chăm sóc da", "skincare", "serum", "kem dưỡng",
    "phòng tập", "gym", "fitness",
]

_GEO_BIDV_RE = re.compile(
    r"(cạnh|gần|bên cạnh|đối diện|trước|sau|cách|100m|200m|50m)"
    r".{0,20}(ngân hàng\s+)?bidv"
    r"|tầng\s*\d+.{0,15}(ngân hàng\s+)?bidv"
    r"|(ngân hàng\s+)?bidv.{0,15}tầng\s*\d+",
    re.IGNORECASE,
)

_CUOI_KW = [
    "đám cưới", "thiệp cưới", "lễ cưới", "hôn lễ",
    "mời cưới", "vu quy", "tân hôn", "wedding",
]

_BANHANG_KW = [
    "inbox", "order", "ship", "giao hàng", "mua hàng", "đặt hàng",
    "ck:", "ck :", "stk:", "stk :", "số tài khoản", "tài khoản ngân hàng",
]

_KIEMTIEN_KW = [
    "bật kiếm tiền", "kiếm tiền trên facebook", "kiếm tiền nội dung",
    "kiếm tiền từ nội dung",
    "#kiemtienfb", "professional mode", "professional dashboard",
    "bật ktnd", "kiếm tiền fb",
]

_THIENNGUYEN_KW = [
    "từ thiện", "thiện nguyện", "nam mô", "quyên góp",
    "ủng hộ", "donate", "hảo tâm",
]

_XINTIEN_KW = [
    "xin tiền", "xin donate", "mạnh thường quân", "mạnh thương quân",
    "ủng hộ em", "giúp em với", "cầu xin", "thương giúp", "giúp đỡ",
]

_PHOTO_KW = [
    "đã thêm ảnh", "add photo", "added a new photo",
    "added photos", "added a photo",
]

_NHAVIA_KW = [
    "nhả vía", "nhả via", "nhả día", "nhả dia",
    "thả qr", "tha qr", "scan qr", "quét qr",
    "xin vía", "xin via", "chia vía", "chia via",
]

_STOCK_KW = [
    "chứng khoán", "thị trường", "cổ phiếu", "stock",
    "securities", "ngân hàng", "bank",
]


# ── MAIN CLASSIFIER ───────────────────────────────────────────────────────────

def classify_bidv_spam(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
    is_post: bool = True,
    channel: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Optional[dict]:
    """
    Apply 16 BIDV spam rules to a single item.

    Parameters
    ----------
    title, content, description : text fields
    is_post    : True if the item is a post/topic; False for comments
    channel    : channel name (e.g. "youtube")
    content_type : type field from SpamRequest (e.g. "youtubeTopic")

    Returns
    -------
    dict  when a rule fires → {"is_spam": bool, "reason": str, "matched_rules": list[str]}
    None  when no rule matches → caller should continue to general spam processing
    """
    title       = (title or "").strip()
    content     = (content or "").strip()
    description = (description or "").strip()

    all_text = (title + " " + content + " " + description).lower()
    tc_text  = (title + " " + content).lower()

    # bidv_check_text: Post → all_text, Comment → content only
    bidv_check_text = all_text if is_post else content.lower()

    # ── R1: Auction + BID ────────────────────────────────────────────────────
    if any(k in all_text for k in ["đấu giá", "phiên đấu", "#daugia", "dau gia"]) \
            and "bid" in all_text:
        return {
            "is_spam": True,
            "reason": "bidv_R1_auction_bid",
            "matched_rules": ["R1: Thảo luận đấu giá + BID"],
        }

    # ── R2: Local service/real-estate + BIDV as landmark ────────────────────
    if any(k in all_text for k in _DV_KW) and _GEO_BIDV_RE.search(all_text):
        return {
            "is_spam": True,
            "reason": "bidv_R2_service_geo_landmark",
            "matched_rules": ["R2: Dịch vụ/BĐS + BIDV là dấu mốc địa lý"],
        }

    # ── R3: Foreign-language characters (CJK / Arabic > 5) ──────────────────
    foreign_chars = re.findall(r"[一-鿿぀-ゟ゠-ヿ가-퟿؀-ۿ]", title + content)
    if len(foreign_chars) > 5:
        return {
            "is_spam": True,
            "reason": "bidv_R3_foreign_language",
            "matched_rules": [f"R3: Tiếng nước ngoài ({len(foreign_chars)} ký tự)"],
        }

    # ── R4: YouTube + BIDV as account number in Description ──────────────────
    _channel = (channel or "").lower()
    _ctype   = (content_type or "").lower()
    is_yt = "youtube" in _channel or "youtube" in _ctype
    if is_yt and _desc_has_bidv_stk(description) and not _has_bidv(tc_text):
        return {
            "is_spam": True,
            "reason": "bidv_R4_youtube_stk_in_desc",
            "matched_rules": ["R4: YouTube - STK BIDV ở Description, title/content không nhắc BIDV"],
        }

    # ── R5: Wedding invitation + BIDV as account number ─────────────────────
    if any(k in all_text for k in _CUOI_KW) and _has_bidv(bidv_check_text):
        return {
            "is_spam": True,
            "reason": "bidv_R5_wedding_stk",
            "matched_rules": ["R5: Mời cưới + BIDV là STK"],
        }

    # ── R6: Commerce + BIDV as account number (requires 6+ digit string) ────
    if any(k in all_text for k in _BANHANG_KW) and _has_bidv(bidv_check_text):
        if re.search(r"bidv.*?\d{6,}|\d{6,}.*?bidv", all_text):
            return {
                "is_spam": True,
                "reason": "bidv_R6_commerce_stk",
                "matched_rules": ["R6: Bán hàng + BIDV là STK"],
            }

    # ── R7: Facebook/social money-earning guide ──────────────────────────────
    if any(k in all_text for k in _KIEMTIEN_KW):
        return {
            "is_spam": True,
            "reason": "bidv_R7_earn_money_guide",
            "matched_rules": ["R7: Hướng dẫn bật kiếm tiền"],
        }

    # ── R8: Charity/donation + BIDV as account number ───────────────────────
    if any(k in all_text for k in _THIENNGUYEN_KW) \
            and (re.search(r"bidv.*?\d{6,}|\d{6,}.*?bidv", all_text)
                 or _has_bidv(bidv_check_text)):
        return {
            "is_spam": True,
            "reason": "bidv_R8_charity_stk",
            "matched_rules": ["R8: Từ thiện/thiện nguyện + BIDV là STK"],
        }

    # ── R9: Event registration + BIDV ───────────────────────────────────────
    if any(k in all_text for k in ["đăng ký tham gia", "đk tham gia",
                                    "form đăng ký", "đăng kí tham gia"]) \
            and _has_bidv(bidv_check_text):
        return {
            "is_spam": True,
            "reason": "bidv_R9_registration_stk",
            "matched_rules": ["R9: Đăng ký tham gia + BIDV là STK"],
        }

    # ── R10: KPI account-opening solicitation ───────────────────────────────
    _r10_context = ["mở tài khoản", "mở tk", "inbox", "liên hệ", "nhắn tin", "zalo"]
    _r10_direct  = any(k in all_text for k in ["hỗ trợ kpi", "kpi mở tài khoản", "nhận kpi"])
    _r10_chay    = "chạy kpi" in all_text and any(k in all_text for k in _r10_context)
    if _r10_direct or _r10_chay:
        return {
            "is_spam": True,
            "reason": "bidv_R10_kpi_account",
            "matched_rules": ["R10: Nhận hỗ trợ KPI mở tài khoản"],
        }

    # ── R11: App target chasing ──────────────────────────────────────────────
    _r11_context  = ["app", "mở tk", "mở tài khoản", "inbox", "liên hệ", "zalo"]
    _r11_direct   = any(k in all_text for k in ["chỉ tiêu app", "chỉ tiêu mở tk"])
    _r11_chay     = "chạy chỉ tiêu" in all_text and any(k in all_text for k in _r11_context)
    if _r11_direct or _r11_chay:
        return {
            "is_spam": True,
            "reason": "bidv_R11_app_target",
            "matched_rules": ["R11: Chạy chỉ tiêu các app"],
        }

    # ── R12: Begging/soliciting money + BIDV ────────────────────────────────
    if any(k in all_text for k in _XINTIEN_KW) and _has_bidv(bidv_check_text):
        return {
            "is_spam": True,
            "reason": "bidv_R12_begging_stk",
            "matched_rules": ["R12: Xin tiền/donate + BIDV là STK"],
        }

    # ── R13: Photo-added post with empty title & content ────────────────────
    if any(k in all_text for k in _PHOTO_KW) \
            and not title.strip() and not content.strip():
        return {
            "is_spam": True,
            "reason": "bidv_R13_photo_empty",
            "matched_rules": ["R13: Thêm ảnh + trống title/content"],
        }

    # ── R14: BIC mentioned without insurance/bank/BIDV context ─────────────
    _check14 = all_text if is_post else tc_text
    if "bic" in _check14 and not any(
        k in _check14 for k in ["bảo hiểm", "insurance", "ngân hàng", "bank", "bidv"]
    ):
        return {
            "is_spam": True,
            "reason": "bidv_R14_bic_no_context",
            "matched_rules": ["R14: Nhắc BIC nhưng không liên quan bảo hiểm/NH/BIDV"],
        }

    # ── R15: BID mentioned without stock/bank/BIDV context ──────────────────
    _check15 = all_text if is_post else tc_text
    if "bid" in _check15 and "bidv" not in _check15 \
            and not any(k in _check15 for k in _STOCK_KW + _BIDV_KEYWORDS):
        return {
            "is_spam": True,
            "reason": "bidv_R15_bid_no_context",
            "matched_rules": ["R15: Nhắc BID nhưng không liên quan chứng khoán/NH/BIDV"],
        }

    # ── R16: Lucky spirit / QR scatter + BIDV ───────────────────────────────
    if any(k in all_text for k in _NHAVIA_KW) and _has_bidv(all_text):
        return {
            "is_spam": True,
            "reason": "bidv_R16_nha_via_qr",
            "matched_rules": ["R16: Nhả vía / Thả QR + BIDV"],
        }

    # No rule matched → fall through to general spam processing
    return None
