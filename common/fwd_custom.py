"""
FWD Insurance custom spam classifier.

Được áp dụng khi index thuộc danh sách FWD_INDICES.
Logic dựa trên các category đặc thù của FWD: logistics, xe cộ, forex,
email forward, gaming, thể thao, brand khác, hình ảnh, tiếng nước ngoài.
"""

import re
from typing import Optional


# ── TRUE BRAND SIGNALS ─────────────────────────────────────────────────────────
TRUE_BRAND_SIGNALS = [
    # Insurance keywords (standalone)
    "nhân thọ", "bảo hiểm", "bảo hiểm nhân thọ", "quyền lợi", "quyền lợi bảo hiểm",
    "bệnh hiểm nghèo", "hợp đồng bảo hiểm", "phí bảo hiểm", "đóng phí", "tái tục",
    "tham gia bảo hiểm", "gói bảo hiểm", "bảo tức", "chi trả bảo hiểm",
    "bồi thường bảo hiểm", "đáo hạn hợp đồng",
    # FWD Brand explicit
    "bảo hiểm fwd", "fwd việt nam", "fwd vietnam", "fwd insurance",
    "hợp đồng fwd", "đóng phí fwd", "claim fwd",
    "đại lý fwd", "agency fwd", "fwd online", "ứng dụng fwd",
    "tuyển dụng fwd insurance",
    # Financial advisory FWD
    "tư vấn tài chính", "bancassurance", "tư vấn bảo hiểm",
    "đại lý bảo hiểm", "đại lý nhân thọ",
    # Bancassurance guard
    "vcb", "vietcombank",
]

# ── CAT-1 & CAT-3: LOGISTICS ──────────────────────────────────────────────────
LOGISTICS_VN = [
    "xuất nhập khẩu", "xnk", "logistics", "giao nhận", "kho bãi", "vận tải",
    "booking tàu", "booking cont", "gom hàng", "hàng air", "hàng sea",
    "thủ tục hải quan", "khai báo hải quan", "vận đơn", "cont lạnh",
    "trucking", "local charge", "cước tàu", "packing list", "co cq",
    "bill of lading", "giá cước", "hãng tàu", "hải quan", "chuỗi cung ứng",
]
LOGISTICS_EN = [
    "freight", "forwarder", "sea freight", "air freight", "customs clearance",
    "shipment", "cargo", "warehouse", "booking note", "inland transport",
    "shipper", "consignee",
]
LOGISTICS_REGEX = [
    r"\bfcl\b", r"\blcl\b", r"\bcont\b",
    r"vận chuyển\s+(?:quốc tế|hàng hóa|container)",
    r"(?:xuất khẩu|nhập khẩu)\s+hàng",
    r"dịch vụ\s+(?:giao nhận|vận tải)",
]
LOGISTICS_JOBS = [
    "sales logistics", "sales xuất nhập khẩu", "ops logistics",
    "nhân viên chứng từ", "điều vận", "hiện trường cảng",
    "logistics executive", "import-export staff", "freight sales",
    "operation executive",
]

# ── CAT-2: XE CỘ ─────────────────────────────────────────────────────────────
CAR_KW = [
    "cầu trước", "dẫn động cầu trước", "front-wheel drive",
    "understeer", "oversteer", "drivetrain", "drag race", "drift xe", "bốc đầu",
]

# ── CAT-4: FOREX ─────────────────────────────────────────────────────────────
FOREX_KW = [
    "hợp đồng kỳ hạn", "tỷ giá kỳ hạn",
    "forward contract", "forward rate", "fx forward", "fx hedging",
    "derivatives", "hợp đồng phái sinh",
]

# ── CAT-5: EMAIL FORWARD ──────────────────────────────────────────────────────
EMAIL_KW = [
    "chuyển tiếp mail", "forward mail", "forwarded message",
    "auto-forward", "fwd email",
]

# ── CAT-6: GAMING ─────────────────────────────────────────────────────────────
GAME_KW = [
    "move forward", "hold fwd", "auto movement", "fps control", "phím điều hướng"
]

# ── CAT-7: THỂ THAO ──────────────────────────────────────────────────────────
SPORT_KW = [
    "tiền đạo", "striker", " cf ", " st ", "fantasy football",
    "fc online", "attacking player", "false 9",
    "fwd pressing", "need fwd cho đội", "xếp fwd",
]

# ── CAT-8: BRAND KHÁC ────────────────────────────────────────────────────────
OTHER_BRAND_KW = [
    "fwd studio", "fwd media", "fwd auto", "fwd tech", "fwd academy",
    "fwd transport", "fwd digital", "digitalfwd",
    "forward digital", "truyền thông forward",
]

# ── CAT-10: IMAGE ONLY ───────────────────────────────────────────────────────
IMAGE_TRIGGERS = ["added new photo", "thêm một ảnh mới", "photos from", "photo by"]

# ── CAT-11: NON-VIETNAMESE ───────────────────────────────────────────────────
VN_WORDS = [
    "của", "và", "là", "có", "không", "được", "này", "với", "trong", "đã",
    "cho", "một", "những", "các", "đến", "từ", "người", "mình", "bạn",
    "họ", "tôi", "ạ", "nhé", "thì", "mà", "nên", "vì", "khi", "như",
    "lại", "đây",
]
VN_CHARS = set(
    "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨ"
    "ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ"
)

# ── DANH SÁCH INDEX ÁP DỤNG FWD CUSTOM ──────────────────────────────────────
FWD_INDICES = {
    "65f0307621a85d74ff2568c1",
    "65f2cec121a85d74ff25692f",
    "65f2d29621a85d74ff256930",
    "65f2d71f21a85d74ff256931",
    "65f3bb4b21a85d74ff256934",
    "65f3bb0421a85d74ff256933",
    "65f3bba821a85d74ff256935",
    "69c3f78f6b551119fb785419",
    "69c4dd9a6b551119fb785563",
    "69c3f8ac6b551119fb78541b",
    "69c3f80c6b551119fb78541a",
    "69c4de2d6b551119fb785565",
}


# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def has_true_brand(text: str) -> bool:
    """Kiểm tra text có chứa tín hiệu thương hiệu FWD thật không."""
    text_lower = text.lower()
    return any(k in text_lower for k in TRUE_BRAND_SIGNALS)


def is_logistics(text: str) -> bool:
    """CAT-1: Logistics/forwarder."""
    text_lower = text.lower()
    if any(k in text_lower for k in LOGISTICS_VN):
        return True
    if any(k in text_lower for k in LOGISTICS_EN):
        return True
    if any(k in text_lower for k in LOGISTICS_JOBS):
        return True
    return any(re.search(p, text_lower) for p in LOGISTICS_REGEX)


def is_car(text: str) -> bool:
    """CAT-2: Xe cộ."""
    text_lower = text.lower()
    return any(k in text_lower for k in CAR_KW)


def is_forex(text: str) -> bool:
    """CAT-4: Forex/forward contracts."""
    text_lower = text.lower()
    return any(k in text_lower for k in FOREX_KW)


def is_email_fwd(text: str) -> bool:
    """CAT-5: Email forwarding."""
    text_lower = text.lower()
    return any(k in text_lower for k in EMAIL_KW)


def is_gaming(text: str) -> bool:
    """CAT-6: Gaming."""
    text_lower = text.lower()
    return any(k in text_lower for k in GAME_KW)


def is_sport(text: str) -> bool:
    """CAT-7: Thể thao/bóng đá."""
    text_lower = text.lower()
    return any(k in text_lower for k in SPORT_KW)


def is_other_brand(text: str) -> bool:
    """CAT-8: Brand khác tên FWD."""
    text_lower = text.lower()
    return any(k in text_lower for k in OTHER_BRAND_KW)


def is_image_only(title: str, content: str, description: str) -> bool:
    """CAT-10: Bài chỉ có hình ảnh, không có text."""
    desc_lower = (description or "").lower()
    title_str = (title or "").strip()
    content_str = (content or "").strip()

    has_image_trigger = any(tr in desc_lower for tr in IMAGE_TRIGGERS)
    is_empty = not title_str and not content_str

    return has_image_trigger and is_empty


def is_non_vietnamese(text: str) -> bool:
    """CAT-11: Nội dung không phải tiếng Việt."""
    text = (text or "").strip()

    if len(text) < 30:
        return False

    text_lower = text.lower()

    if any(f" {w} " in f" {text_lower} " for w in VN_WORDS):
        return False

    vn_char_count = sum(1 for c in text if c in VN_CHARS)
    vn_ratio = vn_char_count / max(len(text), 1)

    return vn_ratio < 0.02


# ── MAIN CLASSIFIER ──────────────────────────────────────────────────────────

def classify_fwd_spam(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
) -> dict:
    """
    Phân loại spam cho các index FWD Insurance.

    Returns:
        {
            "is_spam": bool,
            "reason": str   # label mô tả lý do, rỗng nếu không phải spam
        }
    """
    title = (title or "").strip()
    content = (content or "").strip()
    description = (description or "").strip()

    combined = f"{title} {content} {description}".lower()

    # Tín hiệu thương hiệu thật => KHÔNG phải spam
    if has_true_brand(combined):
        return {"is_spam": False, "reason": "fwd_true_brand"}

    if is_logistics(combined):
        return {"is_spam": True, "reason": "fwd_spam_logistics"}

    if is_car(combined):
        return {"is_spam": True, "reason": "fwd_spam_xe_co"}

    if is_forex(combined):
        return {"is_spam": True, "reason": "fwd_spam_forex"}

    if is_email_fwd(combined):
        return {"is_spam": True, "reason": "fwd_spam_email_forward"}

    if is_gaming(combined):
        return {"is_spam": True, "reason": "fwd_spam_gaming"}

    if is_sport(combined):
        return {"is_spam": True, "reason": "fwd_spam_the_thao"}

    if is_other_brand(combined):
        return {"is_spam": True, "reason": "fwd_spam_brand_khac"}

    if is_image_only(title, content, description):
        return {"is_spam": True, "reason": "fwd_spam_hinh_anh"}

    if is_non_vietnamese(combined):
        return {"is_spam": True, "reason": "fwd_spam_tieng_nuoc_ngoai"}

    return {"is_spam": False, "reason": "fwd_no_match"}
