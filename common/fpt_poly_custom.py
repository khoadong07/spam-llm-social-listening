"""
FPT Polytechnic (Cao đẳng FPT) custom spam classifier.

Applied when index belongs to FPT_POLY_INDICES or FPT_POLY_KBEAUTY_INDICES.

Logic (inverted filter):
  - Nhắc FPT / hệ sinh thái FPT nhưng không có ngữ cảnh Cao đẳng FPT → SPAM
  - Topic Poly K-beauty: Cao đẳng FPT nhưng không có ngữ cảnh K-beauty → SPAM

Returns:
  - dict  when a rule fires
  - None  when no rule matches → caller falls through to general spam processing
"""

import re
from typing import Optional


# ── INDEX SETS ───────────────────────────────────────────────────────────────
FPT_POLY_INDICES = {
    "6409b7c199b95736dad7f1bd",  # FPT Polytechnic
    "649ed7d139627c636da2c3db",  # Cao đẳng Việt Mỹ
    "649edd9339627c636da2c3dc",  # Đại học - Cao đẳng Văn Lang
    "649ede7439627c636da2c3dd",  # Cao đẳng Nova
    "649edfb239627c636da2c3de",  # Cao đẳng CNTT TP HCM
    "649ee07e39627c636da2c3df",  # Cao đẳng Lý Tự Trọng TP HCM
    "666177351312aa2f3ba78f72",  # Poly K-beauty
    "666172aa1312aa2f3ba78f70",  # Melbourne Polytechnic
    "6661741d1312aa2f3ba78f71",  # BTEC FPT Polytechnic
}

# Chỉ topic Poly K-beauty → áp dụng thêm R10-R12
FPT_POLY_KBEAUTY_INDICES = {
    "666177351312aa2f3ba78f72",  # Poly K-beauty
}


# ── KEYWORD LISTS ─────────────────────────────────────────────────────────────
_CAODANG_FPT_KW = [
    "cao đẳng fpt", "fpt polytechnic", "fpt poly", "poly fpt",
    "caodangfpt", "cd fpt", "polytechnic fpt",
    "trường cao đẳng fpt", "cđ fpt",
]

_FPT_UNIVERSITY_KW = [
    "đại học fpt", "fpt university", "fpt edu", "đhfpt", "dh fpt",
    "university fpt", "đại học fpt hà nội", "đại học fpt hcm",
    "đại học fpt đà nẵng", "đại học fpt cần thơ",
]

_FPT_SCHOOL_KW = [
    "fpt school", "fpt schooling", "trường fpt school", "fptschool", "fpt k12",
]

_FPT_TELECOM_KW = [
    "fpt telecom", "fpt internet", "fpt fiber", "mạng fpt",
    "đường truyền fpt", "wifi fpt", "fpt broadband",
    "lắp mạng fpt", "gói cước fpt", "fpt isp",
]

_FPT_PLAY_KW = [
    "fpt play", "fptplay", "fpt cinema", "rạp chiếu fpt",
    "fpt play box", "fpt film", "fpt media",
]

_BH_MEDIA_KW = ["bh media", "bhmedia", "bh entertainment"]

_FPT_CORP_KW = [
    "tập đoàn fpt", "fpt corporation", "fpt group", "fpt software",
    "fpt retail", "fpt is", "fpt information system",
    "fpt japan", "fpt smart cloud", "fpt ai",
    "fpt securities", "fpt digital",
]

_FPT_LEADERS_KW = [
    "hoàng việt anh", "trương gia bình", "nguyễn văn khoa",
    "bùi quang ngọc", "đỗ cao bảo",
]

_FPT_SUBBRAND_KW = [
    "fpt software", "fpt retail", "fpt shop", "fpt camera",
    "fpt smart home", "fpt securities", "fpt digital retail",
    "fpt.vn", "fpt online",
]

_KBEAUTY_KW = [
    "k-beauty", "kbeauty", "k beauty", "poly k-beauty", "poly kbeauty",
    "làm đẹp", "thẩm mỹ", "nail", "spa",
    "trang điểm", "chăm sóc da", "skincare", "makeup",
    "mỹ phẩm", "phun xăm", "lông mày", "mi giả", "nối mi",
    "waxing", "facial", "dưỡng da", "hàn quốc làm đẹp",
    "korean beauty", "k-pop beauty", "esthetics",
    "gội đầu dưỡng sinh", "tạo mẫu tóc", "hair stylist",
    "chăm sóc sắc đẹp", "ngành làm đẹp",
]

_EDUCATION_KW = [
    "tuyển sinh", "xét tuyển", "học bổng", "học phí",
    "sinh viên", "học sinh", "giảng viên", "giáo viên",
    "campus", "ký túc xá", "câu lạc bộ", "clb", "sự kiện trường",
    "lễ tốt nghiệp", "bằng tốt nghiệp", "thực tập",
    "chương trình đào tạo", "ngành học", "khoa",
    "review trường", "trải nghiệm học", "học tại",
]


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _has_caodang_fpt(text: str) -> bool:
    return any(kw in text for kw in _CAODANG_FPT_KW)


def _has_kbeauty(text: str) -> bool:
    return any(kw in text for kw in _KBEAUTY_KW)


# ── MAIN CLASSIFIER ───────────────────────────────────────────────────────────
def classify_fpt_poly_spam(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
    is_post: bool = True,
    site_name: Optional[str] = None,
    content_type: Optional[str] = None,
    index: Optional[str] = None,
) -> Optional[dict]:
    """
    Apply FPT Polytechnic spam rules.

    Returns dict when a rule fires, None when no rule matches (fall-through).
    """
    title       = (title or "").strip()
    content     = (content or "").strip()
    description = (description or "").strip()

    all_text = (title + " " + content + " " + description).lower()
    is_kbeauty_topic = (index or "") in FPT_POLY_KBEAUTY_INDICES

    # Không nhắc FPT và không phải K-beauty topic → không có căn cứ → fall-through
    if "fpt" not in all_text and not is_kbeauty_topic:
        return None

    has_cd_fpt  = _has_caodang_fpt(all_text)
    has_kbeauty = _has_kbeauty(all_text)

    # ── R5: FPT University ───────────────────────────────────────────────────
    if any(k in all_text for k in _FPT_UNIVERSITY_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R5_university",
            "matched_rules": ["R5: Nội dung về FPT University, không liên quan Cao đẳng FPT"],
        }

    # ── R6: FPT School ───────────────────────────────────────────────────────
    if any(k in all_text for k in _FPT_SCHOOL_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R6_school",
            "matched_rules": ["R6: Nội dung về FPT School, không liên quan Cao đẳng FPT"],
        }

    # ── R7: FPT Telecom ──────────────────────────────────────────────────────
    if any(k in all_text for k in _FPT_TELECOM_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R7_telecom",
            "matched_rules": ["R7: Nội dung về FPT Telecom, không liên quan Cao đẳng FPT"],
        }

    # ── R8: FPT Play ─────────────────────────────────────────────────────────
    if any(k in all_text for k in _FPT_PLAY_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R8_play",
            "matched_rules": ["R8: Nội dung về FPT Play, không liên quan Cao đẳng FPT"],
        }

    # ── R4: BH Media ─────────────────────────────────────────────────────────
    if any(k in all_text for k in _BH_MEDIA_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R4_bh_media",
            "matched_rules": ["R4: Nội dung về BH Media, không liên quan Cao đẳng FPT"],
        }

    # ── R2: Tập đoàn FPT / FPT Corporation ──────────────────────────────────
    if any(k in all_text for k in _FPT_CORP_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R2_corporation",
            "matched_rules": ["R2: Nội dung về Tập đoàn FPT, không liên quan Cao đẳng FPT"],
        }

    # ── R3: Lãnh đạo / cá nhân FPT ──────────────────────────────────────────
    if any(k in all_text for k in _FPT_LEADERS_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R3_leader",
            "matched_rules": ["R3: Nhắc lãnh đạo FPT, không liên quan Cao đẳng FPT"],
        }

    # ── R9: Sub-brand FPT khác (catch-all) ───────────────────────────────────
    if any(k in all_text for k in _FPT_SUBBRAND_KW) and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R9_subbrand",
            "matched_rules": ["R9: Nhắc sub-brand FPT, không liên quan Cao đẳng FPT"],
        }

    # ── R1: "FPT" chung chung, không có ngữ cảnh Cao đẳng FPT ───────────────
    if "fpt" in all_text and not has_cd_fpt:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R1_generic_fpt",
            "matched_rules": ["R1: Nhắc FPT chung chung, không liên quan Cao đẳng FPT"],
        }

    # Từ đây: has_cd_fpt = True
    # ── R10+R11: Topic K-beauty — Polytechnic không có K-beauty context ──────
    if is_kbeauty_topic and has_cd_fpt and not has_kbeauty:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R10_11_no_kbeauty",
            "matched_rules": ["R10-11: Nhắc FPT Polytechnic nhưng không liên quan Poly K-beauty"],
        }

    # ── R12: Topic K-beauty — Nội dung giáo dục chung, không K-beauty ────────
    if is_kbeauty_topic and any(k in all_text for k in _EDUCATION_KW) and not has_kbeauty:
        return {
            "is_spam": True,
            "reason": "fpt_poly_R12_education_no_kbeauty",
            "matched_rules": ["R12: Nội dung giáo dục FPT Polytechnic, không liên quan K-beauty"],
        }

    return None
