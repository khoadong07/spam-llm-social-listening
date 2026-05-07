import re
import unicodedata
from typing import Dict, List, Any


def remove_vietnamese_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return text


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = remove_vietnamese_accents(text)
    text = re.sub(r"[^\w\s&+.%/-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_keywords(keywords: List[str]) -> List[str]:
    return [normalize_text(kw) for kw in keywords]


RULES = [
    {
        "rule_id": "R01",
        "rule_name": "charity_donation_bank_account",
        "description": "Quyên góp / từ thiện / hảo tâm, brand chỉ xuất hiện như phương tiện chuyển khoản.",
        "logic": "AND giữa các nhóm, OR trong từng nhóm",
        "keyword_groups": [
            {
                "group_name": "charity_context",
                "keywords": [
                    "quyên góp", "từ thiện", "ủng hộ", "hảo tâm",
                    "mạnh thường quân", "giúp đỡ", "hoàn cảnh khó khăn",
                    "viện phí", "mổ gấp", "tai nạn", "cần hỗ trợ",
                    "xin giúp", "cứu trợ", "thiện nguyện"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "stk", "số tài khoản", "chuyển khoản", "ck",
                    "ngân hàng", "momo", "zalopay", "vietcombank",
                    "techcombank", "mb bank", "bidv", "vietinbank"
                ]
            }
        ]
    },
    {
        "rule_id": "R02",
        "rule_name": "livestream_entertainment_gift_payment",
        "description": "Livestream game / phim / clip giải trí, brand chỉ dùng để donate hoặc nhận quà.",
        "logic": "AND giữa các nhóm, OR trong từng nhóm",
        "keyword_groups": [
            {
                "group_name": "entertainment_context",
                "keywords": [
                    "livestream", "live stream", "xem live", "clip review",
                    "reaction", "tập phim", "tap phim", "phim mới",
                    "game show", "minigame", "nhận quà", "tặng quà",
                    "ủng hộ kênh", "donate"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "stk", "số tài khoản", "chuyển khoản", "ck",
                    "momo", "zalopay", "ngân hàng"
                ]
            }
        ]
    },
    {
        "rule_id": "R03",
        "rule_name": "resell_pass_items_payment",
        "description": "Mua bán / pass đồ / thanh lý, brand chỉ là kênh thanh toán hoặc STK.",
        "logic": "AND giữa các nhóm, OR trong từng nhóm",
        "keyword_groups": [
            {
                "group_name": "selling_context",
                "keywords": [
                    "pass", "pass lại", "thanh lý", "xả hàng",
                    "sale mạnh", "chợ đồ hiệu", "hàng auth",
                    "hàng si", "order", "đặt cọc", "ib giá",
                    "inbox giá", "chốt đơn", "sỉ lẻ"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "stk", "số tài khoản", "chuyển khoản", "ck",
                    "momo", "techcombank", "vietcombank", "ngân hàng"
                ]
            }
        ]
    },
    {
        "rule_id": "R04",
        "rule_name": "bakery_cake_shop",
        "description": "Tiệm bánh / bakery / cake shop, trùng từ khóa cake với brand Cake.",
        "logic": "AND giữa các nhóm, OR trong từng nhóm",
        "keyword_groups": [
            {
                "group_name": "bakery_context",
                "keywords": [
                    "bakery", "cake shop", "tiệm bánh", "bánh kem",
                    "bánh sinh nhật", "bánh ngọt", "cupcake",
                    "bánh bông lan", "decor bánh", "đặt bánh"
                ]
            },
            {
                "group_name": "cake_keyword",
                "keywords": [
                    "cake"
                ]
            }
        ]
    },
    {
        "rule_id": "R05",
        "rule_name": "beauty_spa_cosmetics",
        "description": "Mỹ phẩm / spa / kem dưỡng / tone son, shop hoặc sản phẩm trùng tên brand.",
        "logic": "OR theo nhóm beauty context",
        "keyword_groups": [
            {
                "group_name": "beauty_context",
                "keywords": [
                    "spa", "mỹ phẩm", "kem dưỡng", "serum", "son",
                    "tone son", "màu son", "phun môi", "nối mi",
                    "skincare", "makeup", "trị nám", "trị mụn",
                    "body lotion", "clinic", "beauty", "chăm sóc da"
                ]
            }
        ]
    },
    {
        "rule_id": "R06",
        "rule_name": "baby_mom_store",
        "description": "Tã bỉm / sữa bột / đồ sơ sinh, shop mẹ và bé trùng tên brand.",
        "logic": "OR theo nhóm baby context",
        "keyword_groups": [
            {
                "group_name": "baby_context",
                "keywords": [
                    "tã", "bỉm", "sữa bột", "sữa công thức",
                    "đồ sơ sinh", "mẹ và bé", "baby shop",
                    "bình sữa", "khăn ướt", "xe đẩy",
                    "quần áo trẻ em", "đồ em bé"
                ]
            }
        ]
    },
    {
        "rule_id": "R07",
        "rule_name": "momo_homestay_hotel",
        "description": "Khách sạn / homestay / villa / resort trùng tên Momo.",
        "logic": "Lưu trú AND Momo",
        "keyword_groups": [
            {
                "group_name": "hotel_context",
                "keywords": [
                    "homestay", "hotel", "khách sạn", "villa",
                    "resort", "booking", "đặt phòng",
                    "phòng view biển", "check in", "nghỉ dưỡng",
                    "lưu trú", "airbnb"
                ]
            },
            {
                "group_name": "momo_keyword",
                "keywords": [
                    "momo", "mo mo"
                ]
            }
        ]
    },
    {
        "rule_id": "R08",
        "rule_name": "momo_bus_limousine",
        "description": "Nhà xe / xe khách / limousine / vé xe có chứa Momo.",
        "logic": "Nhà xe AND Momo",
        "keyword_groups": [
            {
                "group_name": "bus_context",
                "keywords": [
                    "nhà xe", "xe khách", "limousine", "vé xe",
                    "đặt vé", "tuyến xe", "xe giường nằm",
                    "bến xe", "đón trả tận nơi"
                ]
            },
            {
                "group_name": "momo_keyword",
                "keywords": [
                    "momo", "mo mo"
                ]
            }
        ]
    },
    {
        "rule_id": "R09",
        "rule_name": "photo_wedding_studio",
        "description": "Studio chụp ảnh / chụp cưới dùng tên brand hoặc chỉ chứa STK.",
        "logic": "OR theo nhóm studio context",
        "keyword_groups": [
            {
                "group_name": "studio_context",
                "keywords": [
                    "studio", "chụp ảnh", "chụp cưới", "ảnh cưới",
                    "pre-wedding", "makeup cô dâu", "váy cưới",
                    "album cưới", "photography", "concept chụp"
                ]
            }
        ]
    },
    {
        "rule_id": "R10",
        "rule_name": "rental_room_bank_account",
        "description": "Phòng trọ / nhà trọ / cho thuê, chỉ chứa STK ngân hàng.",
        "logic": "Phòng trọ AND thanh toán",
        "keyword_groups": [
            {
                "group_name": "rental_context",
                "keywords": [
                    "phòng trọ", "nhà trọ", "cho thuê phòng",
                    "tìm phòng", "ở ghép", "cọc phòng",
                    "tiền phòng", "điện nước", "full nội thất",
                    "gần trường", "gần khu công nghiệp"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "stk", "số tài khoản", "chuyển khoản", "ck",
                    "ngân hàng", "momo", "vietcombank",
                    "techcombank", "mb bank", "bidv"
                ]
            }
        ]
    },
    {
        "rule_id": "R11",
        "rule_name": "novel_story_donation",
        "description": "Truyện / novel / chương dài, brand chỉ xuất hiện ở phần donate hoặc STK.",
        "logic": "Truyện AND donate/thanh toán",
        "keyword_groups": [
            {
                "group_name": "novel_context",
                "keywords": [
                    "truyện", "novel", "chương", "chap",
                    "truyện chữ", "ngôn tình", "đam mỹ",
                    "xuyên không", "huyền huyễn", "tiên hiệp",
                    "đọc truyện", "tác giả", "dịch giả"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "stk", "số tài khoản", "ủng hộ truyện",
                    "donate", "momo", "techcombank", "tcb",
                    "mb bank", "vietcombank"
                ]
            }
        ]
    },
    {
        "rule_id": "R12",
        "rule_name": "anime_figure_preorder_payment",
        "description": "Figure / anime / pre-order / nendoroid, shop bán figure đặt cọc qua ví/ngân hàng.",
        "logic": "Anime/Figure AND thanh toán",
        "keyword_groups": [
            {
                "group_name": "anime_figure_context",
                "keywords": [
                    "figure", "anime", "manga", "nendoroid",
                    "pre-order", "preorder", "order figure",
                    "cọc", "đặt cọc", "goods", "blind box",
                    "mô hình", "waifu", "husbando"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "momo", "techcombank", "tcb", "mb bank",
                    "vietcombank", "chuyển khoản", "stk", "ck"
                ]
            }
        ]
    },
    {
        "rule_id": "R13",
        "rule_name": "fnb_promo_payment_app",
        "description": "F&B promo như KFC, Starbucks, Highlands, GrabFood; brand payment chỉ là liên kết thanh toán.",
        "logic": "F&B AND ví/thanh toán",
        "keyword_groups": [
            {
                "group_name": "fnb_context",
                "keywords": [
                    "kfc", "starbucks", "highlands", "phúc long",
                    "the coffee house", "grabfood", "shopeefood",
                    "baemin", "voucher", "mã giảm giá",
                    "combo", "deal hot", "đặt món", "freeship"
                ]
            },
            {
                "group_name": "payment_app_context",
                "keywords": [
                    "momo", "zalopay", "shopeepay", "viettel money",
                    "banking", "thanh toán qua", "liên kết ví",
                    "cashback", "hoàn tiền"
                ]
            }
        ]
    },
    {
        "rule_id": "R14",
        "rule_name": "gaming_esport_payment",
        "description": "Gaming / Esport / Free Fire / Liên Quân; brand chỉ là phương thức nạp game/thanh toán.",
        "logic": "Gaming AND thanh toán/nạp game",
        "keyword_groups": [
            {
                "group_name": "gaming_context",
                "keywords": [
                    "free fire", "liên quân", "liên minh",
                    "pubg", "valorant", "esport", "gaming",
                    "game", "rank", "skin", "kim cương",
                    "quân huy", "nạp game", "acc game", "bán acc"
                ]
            },
            {
                "group_name": "payment_context",
                "keywords": [
                    "momo", "zalopay", "shopeepay", "banking",
                    "chuyển khoản", "stk", "nạp qua",
                    "thanh toán qua"
                ]
            }
        ]
    },
    {
        "rule_id": "R15",
        "rule_name": "phone_installment_finance",
        "description": "Cửa hàng điện thoại / mua trả góp; Fundiin/Home Credit chỉ là phương thức trả góp.",
        "logic": "Thiết bị điện tử AND trả góp/tài chính",
        "keyword_groups": [
            {
                "group_name": "phone_store_context",
                "keywords": [
                    "điện thoại", "iphone", "samsung", "oppo",
                    "xiaomi", "cửa hàng điện thoại", "laptop",
                    "macbook", "ipad", "máy tính bảng"
                ]
            },
            {
                "group_name": "installment_context",
                "keywords": [
                    "trả góp", "mua trả góp", "duyệt hồ sơ",
                    "hồ sơ trả góp", "góp 0%", "góp hàng tháng",
                    "fundiin", "home credit", "fe credit",
                    "hd saison", "mcredit", "shinhan finance",
                    "trả góp qua"
                ]
            }
        ]
    }
]


def find_keyword_matches(text: str, keywords: List[str]) -> List[str]:
    """
    Trả về danh sách keyword match trong text.
    Đã normalize cả text và keyword.
    """
    norm_keywords = normalize_keywords(keywords)

    matched = []
    for raw_kw, norm_kw in zip(keywords, norm_keywords):
        if norm_kw and norm_kw in text:
            matched.append(raw_kw)

    return matched


def evaluate_rule(text: str, rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Một rule match khi:
    - Tất cả keyword_groups đều match ít nhất 1 keyword.
    - Trong mỗi group: OR logic.
    - Giữa các group: AND logic.
    """

    group_results = []
    is_rule_matched = True

    for group in rule["keyword_groups"]:
        matched_keywords = find_keyword_matches(text, group["keywords"])
        group_matched = len(matched_keywords) > 0

        group_results.append({
            "group_name": group["group_name"],
            "matched": group_matched,
            "matched_keywords": matched_keywords
        })

        if not group_matched:
            is_rule_matched = False

    return {
        "rule_id": rule["rule_id"],
        "rule_name": rule["rule_name"],
        "description": rule["description"],
        "matched": is_rule_matched,
        "group_results": group_results
    }


def detect_spam_by_rules(
    text: str,
    return_all_matches: bool = True
) -> Dict[str, Any]:
    """
    Input:
        text: Nội dung cần kiểm tra.
        return_all_matches:
            True  -> trả về tất cả rule match.
            False -> chỉ trả về rule đầu tiên match.

    Output:
        {
            "is_spam": bool,
            "matched_rule_names": [...],
            "matched_rules": [...]
        }
    """

    normalized = normalize_text(text)

    matched_rules = []

    for rule in RULES:
        result = evaluate_rule(normalized, rule)

        if result["matched"]:
            matched_rules.append(result)

            if not return_all_matches:
                break

    return {
        "is_spam": len(matched_rules) > 0,
        "matched_rule_names": [
            rule["rule_name"] for rule in matched_rules
        ],
        "matched_rules": matched_rules
    }

