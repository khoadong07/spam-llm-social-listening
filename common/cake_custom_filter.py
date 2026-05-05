"""
CAKE by VPBank — Social Listening Spam Filter
==============================================
Phân loại bài đăng liên quan đến CAKE (VPBank fintech) vs bánh thật / nội dung không liên quan.

Logic 3 bước:
  1. FINTECH keywords mạnh  → is_spam = NO  (CAKE_FINTECH)
  2. BAKERY keywords mạnh   → is_spam = YES (BAKERY)
  3. Nội dung không liên quan → is_spam = YES (UNRELATED)

Usage:
    from common.cake_custom_filter import classify_row
    
    row_data = {
        "Title": "...",
        "Content": "...",
        "Description": "..."
    }
    
    is_spam, reason = classify_row(row_data)
"""

# =============================================================================
# KEYWORD LISTS — chỉnh sửa tại đây để cập nhật rules
# =============================================================================

# Nhóm 1: CAKE VPBank fintech → KHÔNG phải spam
FINTECH_STRONG = [
    "vpbank", "cakebyvpbank", "#cakebyvpbank", "#proudofcake",
    "huy động", "số dư", "bi team", "fintech", "kỳ lân", "unicorn",
    "triệu user", "triệu khách hàng", "nghìn tỷ", "15.000 tỷ",
    "10.000 tỷ", "1.000 tỷ", "app mới launch", "cake app",
    "team cake", "cả team cake", "sản phẩm ở cake", "happy birthday cake !!!",
]

# Nhóm 2: Tiệm bánh / ngành bánh → SPAM (BAKERY)
BAKERY_STRONG = [
    "tiệm bánh", "đặt bánh", "giao bánh", "ship bánh", "bánh kem",
    "bánh sinh nhật", "thổi nến", "lấy gấp", "cốt bánh",
    "kem sữa tươi", "bông lan", "mousse", "tiramisu", "panna cotta",
    "bánh rút tiền", "gato", "gatô", "entremet", "cheesecake",
    "bánh bento", "bánh mousse", "bánh vẽ", "bánh in ảnh",
    "bánh cưới", "bánh thôi nôi", "bánh mừng thọ",
    "nhận đặt bánh", "order bánh", "ship tận nơi",
    "thanh toán khi nhận", "lấy ngay",
    "#banhsinhnhat", "#banhkem", "#tiembanhshincake",
    "#makicake", "baking is love", "birthday cake",
    "wedding cake", "butter cake", "chocolate cake",
    "fruit cake", "marble cake", "cup cake",
    # Thêm variants không dấu
    "banh kem", "banh sinh nhat", "tiem banh", "kem sua tuoi",
    "banhkem", "banhsinhnhat", "tiembanh", "kemsuatuoi",
    "kica bakery", "bakery", "cake shop",
    # Thêm từ khóa giảm giá tiệm bánh
    "giảm 50%", "giảm 50k", "giá bánh", "thanh toán",
]

# Nhóm 3: Nội dung hoàn toàn không liên quan → SPAM (UNRELATED)
OTHER_SPAM = [
    "hải sản", "buffet", "huda beauty", "phấn phủ", "mỹ phẩm",
    "yến sào", "khánh hòa", "gozyuger", "tokusatsu", "super sentai",
    "anime", "kamen rider", "highlands coffee", "voucher",
    "party shop", "balloon", "decoration", "tuyển dụng", "kế toán",
    "vốn kinh doanh", "rice cake shop", "drug rice cake",
    "flipbook", "công thức bánh", "cheft",
    "srilanka", "rathnapura", "chilaw",
    "bake loose", "setting powder", "loose baking",
]


# =============================================================================
# CLASSIFICATION LOGIC
# =============================================================================

def classify_row(row_dict: dict) -> tuple:
    """
    Phân loại một dòng dữ liệu dựa trên Title + Content + Description.

    Args:
        row_dict: Dictionary với keys "Title", "Content", "Description"

    Returns:
        (is_spam, spam_reason)
        is_spam      : "YES" hoặc "NO"
        spam_reason  : "CAKE_FINTECH" | "BAKERY" | "UNRELATED" | "UNKNOWN"
    """
    text = " ".join([
        str(row_dict.get("Title", "") or ""),
        str(row_dict.get("Content", "") or ""),
        str(row_dict.get("Description", "") or ""),
    ]).lower()
    
    # Debug: Print first 200 chars of text
    print(f"🔍 CAKE Filter - Text preview: {text[:200]}...")

    # Bước 1: FINTECH → không spam
    for kw in FINTECH_STRONG:
        if kw.lower() in text:
            print(f"✅ FINTECH keyword matched: {kw}")
            return "NO", "CAKE_FINTECH"

    # Bước 2: BAKERY → spam
    matched_bakery = []
    for kw in BAKERY_STRONG:
        if kw.lower() in text:
            matched_bakery.append(kw)
    
    if matched_bakery:
        print(f"🍰 BAKERY keywords matched: {matched_bakery[:5]}")  # Show first 5
        return "YES", "BAKERY"

    # Bước 3: Nội dung khác → spam
    for kw in OTHER_SPAM:
        if kw.lower() in text:
            print(f"🚫 UNRELATED keyword matched: {kw}")
            return "YES", "UNRELATED"

    print(f"❓ No keywords matched - returning UNKNOWN")
    return "NO", "UNKNOWN"
