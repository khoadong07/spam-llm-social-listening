"""
GHN (Giao Hang Nhanh) custom spam classifier.

Duoc ap dung khi index thuoc danh sach GHN_INDICES.
Logic tai su dung toan bo GHN spam filter v10 tu test_ghn.py,
boc trong cung interface voi fwd_custom.py.
"""

import re
from typing import Optional


# ── DANH SACH INDEX AP DUNG GHN CUSTOM ──────────────────────────────────────
GHN_INDICES = {
    "6061ab828afb7ad66c737436",
    "6066d6a6f6c7a9a132b22f59",
    "6066f842f6c7a9a132b24628",
    "6066faa7f6c7a9a132b24e8d",
    "606af5bff6c7a9a132b448ae",
    "606af864f6c7a9a132b4492f",
    "61b9915699ce4372a5d739eb",
    "6263ddb21a666a5fa61651cb",
    "6263d2ee1a666a5fa61651c9",
    "63c6241e03c39417860b28e2",
    "686219ab398f863c83be8d3c",
}


# ============== Layer 0: GHN Community whitelist ==============
GHN_COMMUNITY_WHITELIST = [
    r'tâm sự giao hàng.*ghn',
    r'khiếu nại giao hàng nhanh',
    r'khiếu nại.*\bghn\b',
    r'bóc phốt giao hàng nhanh',
    r'bóc phốt.*\bghn\b',
    r'^giao hàng nhanh$',
    r'^giao hàng nhanh\s*[-–]\s*ghn',
    r'review.*đơn vị vận chuyển',
    r'tìm đơn vị vận chuyển',
    r'tuyển dụng.*giaohangnhanh',
    r'tuyển dụng.*\bghn\b',
    r'\bghn\b.*tuyển dụng',
    r'hội ae giao hàng.*\bghn\b',
    r'cộng đồng.*giao hàng nhanh',
    r'hỗ trợ.*đồng giá.*vận chuyển',
    r'không phốt ở đây',
    r'tiếp nhận phản hồi.*giao hàng nhanh',
    r'bigsize ship.*review.*đơn vị',
]


# ============== Brand strong ==============
GHN_BRAND_STRONG = [
    r'\bghn\.vn\b', r'\bgiaohangnhanh\.vn\b',
    r'bưu cục\s+ghn', r'shipper\s+ghn', r'nhân viên\s+ghn',
    r'tài xế\s+ghn', r'app\s+ghn', r'ứng dụng\s+ghn',
    r'\[ghn\]',
    r'giao hàng nhanh\s*[-–]\s*ghn',
    r'giao hàng nhanh\s+(express|jsc|đồng giá|corporation)',
    r'công ty\s+(cổ phần\s+|tnhh\s+|cp\s+)?giao hàng nhanh',
    r'giao hàng nhanh[^\n]{0,30}(hoàn tiền|khiếu nại|sự cố|mất hàng|thất lạc|bồi thường)',
    r'(khiếu nại|bóc phốt|phốt|review)[^\n]{0,30}giao hàng nhanh',
    r'(khiếu nại|bóc phốt|phốt|review)[^\n]{0,30}\bghn\b',
    r'lên đơn\s+(qua\s+|với\s+|bên\s+)?giao hàng nhanh',
    r'tiếp nhận phản hồi giao hàng nhanh',
    r'đơn vị vận chuyển\s+\bghn\b',
    r'\bghn\b\s*(express|jsc)',
    r'cộng đồng\s+(\w+\s+){0,3}\bghn\b',
    r'giao hàng nhanh[^\n]{0,20}tuyển\s+(dụng|shipper|gấp|nhân viên)',
]


# ============== San pham / Categories ==============
PRODUCT_CATEGORIES = (
    r'(cút inox|phụ kiện inox|kho inox|inox 304|inox thực phẩm|clamp inox'
    r'|hàn thép|hàn inox|hàn xì|gia công thép'
    r'|mái nhôm|mái tôn|tấm lợp|nhà máy.*nhôm'
    r'|sắt thép|thép cuộn|pallet|thuỷ lực|chống thấm|giàn giáo|coppha'
    r'|gạch ốp|gạch men|đá ốp|ốp tường|chai pet|ly giấy|cốc nhựa'
    r'|túi nilon|in túi|bao bì'
    r'|cát xây dựng|keo silicone|sun wood|sunny wood|gỗ nhựa|tấm compact|hpl'
    r'|midea|daikin|casper|panasonic|electrolux|aqua|máy lạnh|điều hòa|inverter'
    r'|tủ lạnh|máy giặt|máy nén|danfoss|fujie|fujihome|limina plaza'
    r'|lò vi sóng|nồi cơm điện|máy lọc nước|máy làm sữa|bình đun siêu tốc'
    r'|tivi samsung|máy làm mát'
    r'|apple watch|iphone|ipad|samsung galaxy|airpods|tai nghe'
    r'|nước hoa|son môi|son lì|kem dưỡng|serum|toner|sữa rửa mặt'
    r'|mặt nạ\b|tẩy trang|kem chống nắng|lông mi|nối mi|mỹ phẩm'
    r'|kem trị nám|multivital kids|wonder bath|kim cosmetic|sữa gạo cosy'
    r'|nhẫn vàng|nhẫn bạc|bông tai|hoa tai|vòng tay|dây chuyền|lắc tay'
    r'|nhẫn kim cương|nhẫn ruby|nhẫn 18k|dây chuyền 18k'
    r'|trang sức|silver|an khang silver|pnj|tiệm vàng'
    r'|cốm mễ trì|gạo đài thơm|gạo st25|bún bò|cơm tấm|phở khô'
    r'|trà sữa|cà phê.*hạt|nem chua|nem giòn|chả lụa|chả mực'
    r'|bánh ngọt|bánh kem|bánh trung thu'
    r'|bún thịt nướng|cơm rang|mỳ cay|mỳ xào|chân gà'
    r'|tôm nõn|hải sản tươi|cá hồi|mực một nắng|tép khô'
    r'|đặc sản|nông sản|trái cây|hoa quả nhập|sầu riêng'
    r'|hoa quả.*bổ.*gọt|hoa quả.*gọt sẵn|trái cây.*gọt sẵn'
    r'|dừa tươi|sâm tươi|dalat milk|nguyên liệu pha chế|h2 power fruits'
    r'|sữa bột|sữa chua|vinamilk|hipp|mochi.*baby|sữa công thức|probi|dielac'
    r'|gà ủ muối|gà bó xôi|gà ôm trứng|gà giòn'
    r'|đồ ăn đêm|đồ ăn vặt|combo ăn'
    r'|nước giặt|nước rửa chén|nước lau sàn'
    r'|hoa tươi|cây giống|cây cảnh|hạt giống|mận hồng đào|cây ăn quả'
    r'|hoa tang lễ|vòng hoa|bó hoa|shophoa|shop hoa|hoa xinh'
    r'|hoa khai trương|hoa đám ma|hoa đám tang|hoa viếng|hoa chia buồn|kệ hoa'
    r'|rượu vang|vali nhựa|tủ nhựa|ghế nhựa|ghế gấp'
    r'|sơn dầu|sơn nhà|than nướng|bếp nướng'
    r'|order trung quốc|hàng quảng châu|hàng nhập khẩu|hàng xách tay'
    r'|thuốc giảm cân|thực phẩm chức năng|tpcn|collagen'
    r'|toyota camry|toyota hilux|toyota veloz|kia sedona|hyundai santafe'
    r'|phụ tùng.*xe|phụ tùng ô tô|thước lái|cọc lái|phanh abs'
    r'|đèn năng lượng mặt trời|đèn nlmt|đèn mặt trời|điện mặt trời'
    r'|quần áo bảo hộ|áo thun đồng phục|in logo theo yêu cầu'
    r'|vinhomes grand park|vinhomes ocean park|căn hộ vinhomes|shophouse vinhomes'
    r'|bảng viết bút lông|bảng từ|bàn ghế học sinh|thiết bị giáo dục|bavico'
    r'|rich kids|combo sơ sinh|đồ sơ sinh|bim sữa'
    r'|chứng khoán|vinanet|diendanchungkhoan'
    r'|mỹ nghệ gỗ|mây nhựa|sàn nhựa|đồ nội thất'
    r'|gas south|petrolimex|petrovietnam gas|total gas|elf gas|saigon petro'
    r'|gas xanh|phúc lộc thọ gas|bình\s*12\s*kg|bình\s*45\s*kg'
    r'|gas chính hãng|bình bò|petrovietnam'
    r'|khô cá|cá lóc.*nắng|cá khô|cá phơi|hải sản phơi'
    r'|tấm ốp nano|nano hd|phào chỉ pu|băng quấn chống ăn mòn'
    r'|tấm ốp tường|ốp trần|phào chỉ'
    r'|phở cuốn|phở khô\b|bánh phở'
    r'|chống ăn mòn|băng quấn'
    r'|gửi hàng đi (mỹ|úc|hàn|nhật|sing|canada|đức|new zealand|nước ngoài)'
    r'|chuyển hàng (đi|về|từ) (mỹ|úc|usa|aus|nhật|hàn|nước ngoài)'
    r'|gửi hàng (mỹ|úc|usa|aus)[\s-]+việt|gửi hàng quốc tế'
    r'|vận chuyển (hàng )?(quốc tế|mỹ-việt|úc-việt|hàn-việt|nhật-việt)'
    r'|dịch vụ chuyển hàng quốc tế|chuyển phát quốc tế'
    r'|viet usa service|chuyển phát quốc tế'
    r'|nệm (cao su|lò xo|foam|pu|topper|massage|gấp)'
    r'|kho nệm|nệm pu\b'
    r'|giao nước (tận nhà|đến nhà|miễn phí|tại nhà)'
    r'|đại lý nước (uống|suối|tinh khiết|lavie|aquafina)'
    r'|nước uống.*đóng bình|nước đóng bình.*giao'
    r'|\bđấu giá\b'
    r'|phiên đấu giá|sàn đấu giá|bước giá|giá khởi điểm'
    r'|xe tải van|xe tải.*thaco|xe khách.*chính hãng'
    r'|phớt (thủy lực|chặn dầu|làm kín|vintin|nok)\b'
    r'|gioăng phớt|gioangphot'
    r'|mực (khô|một nắng).*(ngon|to|dày|chất)'
    r'|mực siêu (to|dày|chất|tươi)|mực\s+khô\s+vintin'
    r'|bàn ghế ăn.*(nhập khẩu|cao cấp|hiện đại)'
    r'|bàn đá ceramic|ghế da xương cá|nội thất nhà bếp nhập khẩu'
    r'|hỏa tốc 247|hoả tốc 247|ship hỏa tốc|ship hoả tốc'
    r'|hỏa tốc.*ứng dụng|app hỏa tốc|ứng dụng hỏa tốc'
    r')\b'
)


PRICE_PATTERNS = (
    r'\d{1,3}k\b|\d{1,3}\.000đ?|\d{1,3}\.\d{3}đ?'
    r'|giá chỉ|giá còn|giá rẻ|giá sỉ|giá tốt|chỉ \d|combo \d'
    r'|trả góp|0%|sale\b|giảm giá|khuyến mãi'
    r'|trả góp lãi suất 0%|trả góp 0%'
)


CONTACT_PATTERNS = (
    r'hotline:?\s*\d|0\d{9,10}\b|zalo:?\s*\d?|\binbox\b|\balo\b'
    r'|inbox\s+(để\s+)?đặt|inbox\s+đặt hàng|inbox\s+(shop|nhé|ngay|order|tư vấn)'
    r'|đặt hàng ngay|đặt ngay|order ngay|mua ngay|liên hệ ngay'
    r'|ib (shop|nha|nhé|em|chị|mình|đặt|order|tư vấn)|fanpage|fb\.com'
    r'|tư vấn (miễn phí|trực tiếp|ngay|24/7|tận tình|nhiệt tình)'
    r'|tư vấn\s+và\s+(báo giá|đặt hàng)'
    r'|báo giá\s+(miễn phí|chi tiết|nhanh)'
    r'|0\d{2,3}[.\-]\d{2,4}[.\-]\d{2,4}'
    r'|\bgiao hàng nhanh\s*[:–\-]\s*0\d'
    r'|\bgiao hàng nhanh\s*[:–\-]\s*\d'
)


EMOJI_MARKERS = (
    r'📞|📍|🔥|🌟|👉|👇|👈|🛒|🚚|✅|🔗|🍀|☀️|🍗|🍜'
    r'|✨|💯|🎯|💸|🏷️|🚀|⚡|👜|💄|👗|🌸|🌺|💐|🎁'
)


CTA_DESCRIPTOR_GHN = (
    r'giao hàng nhanh\s*[-–,]\s*(nóng hổi|tận nơi|tận tay|miễn phí|toàn quốc|chính hãng|uy tín|gọn|kín đáo|sạch)'
    r'|miễn phí.*giao hàng nhanh'
    r'|giao hàng nhanh\s+toàn quốc'
    r'|giao hàng nhanh\s+(chóng|tận (nhà|nơi|tay)|miễn phí)'
    r'|cam kết giao hàng nhanh'
    r'|📍\s*giao hàng nhanh|🚚\s*giao hàng nhanh'
    r'|\bship nhanh\b|\bship toàn quốc\b|\bship (tận nhà|tận nơi|tận tay|miễn phí)\b'
    r'|\bgiao ngay\b|\bgiao nhanh\b|\bgiao tận (nhà|nơi|tay)\b'
    r'|\bgiao trong ngày\b|\bgiao 2h\b|\bgiao siêu tốc\b'
    r'|\bhàng (có )?sẵn\b|\bcó sẵn (hàng|kho)\b|\bsẵn kho\b|\bsẵn hàng\b'
)


# ============== SPAM SITE patterns ==============
SPAM_SITE_PATTERNS = [
    r'\bpnj\b', r'tiệm vàng', r'trang sức',
    r'\bsilver\b', r'an khang silver', r'jewelry',
    r'ăn vặt\b', r'\bcốm\b', r'hải sản\b', r'trái cây\b', r'hoa quả\b',
    r'than nướng', r'thực phẩm\b', r'đặc sản\b', r'nông sản',
    r'đồ ăn đêm', r'quán nhậu', r'quán ăn\b', r'mộc sơn quán',
    r'organic', r'taphoa', r'tạp hóa',
    r'bán cà phê', r'daysom.*cafe', r'daysombancaphe',
    r'nemgiare', r'chăn nuôi.*heo', r'heo giống',
    r'mochi baby', r'cake by', r'minh phương store',
    r'mỹ ý shop', r'caygiong', r'cây giống',
    r'đann organic', r'mongthu', r'caphe.*mangdi',
    r'july tan', r'cakebychloe',
    r'hoa quả.*bổ.*sẵn', r'hoa quả.*gọt sẵn', r'trái cây.*gọt sẵn',
    r'fruit.*box', r'h2 power fruits',
    r'vải lót\b', r'vải địa kỹ thuật',
    r'thép\b', r'sắt thép', r'pallet nhựa', r'thuỷ lực\b', r'\bgạch\b',
    r'nón bảo hiểm\b', r'giày bảo hộ', r'chống thấm\b',
    r'giàn giáo', r'coppha\b', r'\binox\b',
    r'tổng kho.*inox', r'kho phụ kiện', r'phụ kiện inox',
    r'hàn thép', r'hàn inox', r'cơ khí.*hàn', r'gia công.*thép',
    r'xưởng\b', r'máy in\b', r'máy in đơn hàng',
    r'mái nhôm', r'mái tôn', r'nhà máy.*nhôm',
    r'v\.ng\.nh\.my\.nhm',
    r'sun wood', r'sunny wood', r'foodmax', r'tấm compact',
    r'đèn năng lượng mặt trời', r'đèn nlmt', r'điện mặt trời',
    r'đèn mặt trời', r'việt nhật.*đèn',
    r'điện máy\b', r'siêu thị điện', r'dienmaycholon', r'fpt shop',
    r'dienmayhoanghai', r'dienmayxanh', r'fu hòa lạc',
    r'winmart\b', r'limina plaza', r'fujie', r'fujihome',
    r'điện máy mạnh cường', r'điện máy phượng vàng',
    r'hoa tang lễ', r'hoa tươi\b', r'tiệm hoa\b', r'cửa hàng hoa\b',
    r'chợ hoa tươi', r'shop hoa\b', r'shophoa\b', r'hoa xinh\b',
    r'vòng hoa đám tang', r'hoa khai trương', r'hoa viếng',
    r'xe ghép\b', r'xe tải\b', r'grab xe\b', r'xe ôm grab', r'taxi\b',
    r'chành xe\b', r'dịch vụ xe\b',
    r'vận chuyển hòa phát', r'ship247\b', r'maxnow\b', r'max now\b',
    r'dang binh express',
    r'thanhlong logistics', r'logistics.*malaysia', r'tapl logistic',
    r'hội ae giao hàng shopee',
    r'shopee express', r'spx việt nam',
    r'người dùng vn post',
    r'phụ tùng.*ô tô', r'phụ tùng xe', r'auto parts\b', r'phụ tùng.*nhập khẩu',
    r'toyota camry', r'kia sedona', r'hyundai santafe',
    r'bếp nướng', r'laser.*cnc', r'máy laser', r'sàn giao dịch xương rồng',
    r'\bmỹ phẩm\b', r'\bcosmetic\b', r'beauty store', r'chợ mỹ phẩm',
    r'wonder bath', r'kim cosmetic',
    r'chợ trời',
    r'chợ\s+(cư dân|mua bán|hải châu|kỳ bá|phú đô|nghĩa tân|thanh xuân|tây)',
    r'chợ\s+(ăn vặt|hoa tươi|vật liệu|bình châu|cốc nhựa|pallet)',
    r'cư dân vinhomes', r'vinhomes grand park', r'vinhomes ocean park',
    r'khu đô thị', r'khu tái định cư', r'cộng đồng cư dân',
    r'nhóm ship đồ ăn',
    r'diendanchungkhoan', r'lamchame\.com', r'techrum\.vn', r'xaluanvn',
    r'\bđhqghn\b', r'vinanet',
    r'club ford', r'hội xe\b', r'hyundai.*club', r'toyota.*club',
    r'hội sơn dầu', r'sơn công nghiệp',
    r'phôi thổi chai', r'chai nhựa\b', r'ly nhựa.*ly giấy', r'cốc nhựa',
    r'in túi\b', r'túi nilon\b',
    r'rich kids', r'đồ sơ sinh', r'combo sơ sinh',
    r'bavico', r'thiết bị giáo dục', r'bàn ghế học sinh',
    r'giỏ quà tết', r'quà tặng doanh nghiệp', r'set quà tết',
    r'kho túi zipper', r'túi zipper', r'túi hút chân không',
    r'gia vị đồ khô', r'mắc khén', r'hạt dổi', r'hạt tiêu',
    r'hoa hồi', r'bào ngư',
    r'nước khoáng lavi', r'nước uống lavi', r'lavie.*đóng bình',
    r'tải chở thuê', r'xe tải.*chở thuê', r'\bxe ôm grab\b',
    r'dọn nhà trọn gói', r'dọn trọ', r'shipper.*siêu tốc',
    r'shipper.*cần thơ',
    r'rao vặt.*cần thơ', r'nhà trọ.*sinh viên', r'phòng trọ cần thơ',
    r'công nhân kcn',
    r'backlink.*social', r'backlink.*báo', r'pr báo', r'support seo',
    r'giầy.*bảo hộ', r'ủng da.*bảo hộ', r'bán buôn sỉ',
    r'rượu vang', r'hàng xách tay',
    r'cho thuê giàn giáo', r'hiệp hội giàn giáo',
    r'shopee\.vn\b', r'hội xe tải.*tìm hàng',
    r'đèn trang trí\b', r'mua sắm sành điệu',
    r'báo đen logistics', r'wacom store',
    r'plxh\.vn', r'phapluatxahoi',
    r'viet usa service',
    r'kho nệm',
    r'phớt\s*(bơm|nok|vintin)',
    r'mực khô',
    r'ban_an_thu_hang',
    r'hỏa tốc 247',
    r'hoả tốc 247',
    r'ship hoả tốc',
    r'ship hỏa tốc',
    r'auto tải.*bus',
    r'tổng kho.*nệm',
]


# ============== SPAM CONTENT patterns ==============
SPAM_CONTENT_PATTERNS = [
    r'\bpnj\b',
    r'puhong việt nam', r'dang binh express',
    r'tôm nõn tươi', r'#hảisảntươi', r'#hảisảnngon',
    r'đồ ăn đêm lào cai',
    r'vải lót chất lượng cao', r'vải địa kỹ thuật',
    r'than nướng.*không khói', r'đèn pha led',
    r'\bnhẫn vàng\b', r'\bbông tai\b', r'\bhoa tai\b', r'\bvòng tay\b',
    r'\bnhẫn kim cương\b', r'\bnhẫn ruby\b', r'\bnhẫn 18k\b',
    r'\bdây chuyền vàng\b', r'\bdây chuyền 18k\b', r'\bvòng tay vàng\b',
    r'làm sạch trang sức miễn phí',
    r'bài poker', r'bài nhựa',
    r'hoa tang lễ.*đặt hàng',
    r'trả góp 0%.*24 ngân hàng.*giao hàng nhanh miễn phí',
    r'giao hàng nhanh miễn phí.*trả góp 0%.*24 ngân hàng',
    r'phụ tùng.*nhập khẩu.*giao hàng nhanh toàn quốc',
    r'diendanchungkhoan', r'vinanet\.vn', r'\bchứng khoán\b',
    r'#hangxachtay.*#giaohangnhanh',
    r'\bship247\b', r'\bmaxnow\b', r'\bmax now\b', r'tapl logistic',
    r'giao hàng nhanh tróng',
    r'cút inox', r'phụ kiện inox', r'inox thực phẩm', r'inox 304',
    r'mái nhôm', r'tấm lợp.*nhôm',
    r'midea inverter', r'casper inverter',
    r'mochi baby', r'sữa.*mochi',
    r'cây giống.*toàn quốc', r'mận hồng đào',
    r'gà ủ muối', r'gà bó xôi', r'mỳ cay 7 cấp',
    r'nem giòn', r'nem chua đà nẵng',
    r'an khang silver',
    r'cốm mễ trì.*đặc sản',
    r'gạo đài thơm', r'gạo st25.*combo',
    r'thuốc.*collagen.*chính hãng',
    r'order.*quảng châu', r'hàng quảng châu',
    r'#shipper.*#banhangonline',
    r'#kingcongkenh', r'#caygiongphuc',
    r'inbox\s+(để\s+)?đặt\s+hàng',
    r'inbox\s+đặt',
    r'hoa quả\s+bổ\s+gọt\s+sẵn',
    r'hoa quả\s+(đã\s+)?gọt\s+sẵn',
    r'trái cây\s+gọt\s+sẵn',
    r'\bhàn thép\b', r'hàn\s+(inox|sắt|xì)',
    r'gia công\s+(hàn|thép|inox|cơ khí)',
    r'giao hàng nhanh\s+toàn\s+quốc',
    r'giao hàng nhanh\s+chóng',
    r'\bship\s+nhanh\b',
    r'\bship\s+toàn\s+quốc\b',
    r'ship\s+(tận\s+nhà|tận\s+nơi|tận\s+tay|miễn\s+phí)',
    r'\bgiao\s+ngay\b', r'\bgiao\s+nhanh\b',
    r'giao\s+(trong ngày|2h|siêu tốc|hỏa tốc)',
    r'\bhàng\s+(có\s+)?sẵn\b',
    r'\bsẵn\s+(hàng|kho)\b',
    r'có\s+sẵn\s+(hàng|kho|tại)',
    r'\bshophoa\b', r'\bhoa\s+xinh\b',
    r'tư vấn\s+(miễn phí|trực tiếp|24/7|tận tình|nhiệt tình|và đặt hàng|và báo giá)',
    r'tư vấn\s+ngay',
    r'\bib\s+tư vấn\b', r'inbox\s+tư vấn',
    r'chân gà chiên', r'chân gà sốt thái', r'\bmỳ xào\b', r'cơm rang\b',
    r'bún thịt nướng', r'\bbún bò huế\b',
    r'h2 power fruits', r'bã mía ủ hoai', r'sâm tươi hàn quốc',
    r'dừa tươi sơ chế', r'dalat milk', r'nguyên liệu pha chế',
    r'nông sản toàn quốc',
    r'\bfujie\b', r'\bfujihome\b', r'limina plaza',
    r'\belectrolux\b', r'\baqua\b.*(máy|tủ|điều hòa)',
    r'điều hòa di động', r'bình đun siêu tốc', r'tivi samsung',
    r'máy làm mát không khí',
    r'\bkia sedona\b', r'thước lái', r'cọc lái', r'phanh abs',
    r'phụ tùng nhập khẩu chính hãng xe',
    r'sun wood', r'sunny wood', r'gỗ nhựa xanh',
    r'cát xây dựng', r'keo silicone a500',
    r'dầu bánh răng thực phẩm', r'foodmax gear',
    r'tấm compact hpl', r'sóng nhựa\b',
    r'kem trị nám', r'multivital kids', r'wonder bath',
    r'kim cosmetic', r'sữa gạo cosy white', r'đau nhức xương khớp',
    r'shopee\.vn', r'dienmaycholon\.com', r'dienmayxanh\.com',
    r'sữa đặc tài lộc', r'\bvinamilk\b', r'sữa bột dielac', r'\bprobi\b',
    r'vinhomes grand park', r'vinhomes ocean park',
    r'căn hộ vinhomes', r'shophouse vinhomes',
    r'bảng viết bút lông', r'\bbảng từ\b', r'bàn ghế học sinh',
    r'bảng 5 điều bác hồ', r'\bbavico\b', r'thiết bị giáo dục',
    r'rich kids', r'combo sơ sinh', r'đồ sơ sinh', r'bim sữa',
    r'\bđèn nlmt\b', r'đèn mắt ngọc', r'đèn năng lượng mặt trời việt nhật',
    r'quần áo bảo hộ lao động', r'áo thun đồng phục',
    r'in logo theo yêu cầu',
    r'hoa khai trương', r'hoa đám ma', r'hoa đám tang', r'hoa viếng',
    r'hoa chia buồn', r'kệ hoa khai trương', r'vòng hoa viếng',
    r'\btiệm hoa\b', r'\bđặt hoa\b',
    r'mỹ nghệ gỗ', r'\bmây nhựa\b', r'\bsàn nhựa\b', r'đồ nội thất',
    r'\bgiá vàng\b',
    r'ship gì cũng có', r'giao hàng siêu tốc',
    r'tải chở thuê', r'xe tải chở thuê',
    r'giỏ quà tết', r'quà tặng doanh nghiệp',
    r'túi zipper', r'túi hút chân không',
    r'gia vị đồ khô', r'mắc khén', r'hạt dổi',
    r'\bbào ngư\b',
    r'nước khoáng lavie', r'nước uống lavi', r'lavie.*đóng bình',
    r'dọn nhà trọn gói', r'dọn trọ',
    r'\bxe ôm grab\b',
    r'rao vặt.*cần thơ',
    r'backlink.*báo', r'support seo',
    r'giầy.*ủng da', r'ủng da.*bảo hộ',
    r'cnc.*nan xoan',
    r'giao hàng nhanh\s*[:–\-]\s*0\d',
    r'giao hàng nhanh\s+0\d{2,3}[.\-]\d',
    r'viettel\s*post.*giao hàng nhanh',
    r'giao hàng nhanh.*viettel\s*post',
    r'\bj\s*&\s*t\b.*giao hàng nhanh',
    r'giao hàng nhanh.*\bj\s*&\s*t\b',
    r'\bjt\s+express\b.*giao hàng nhanh',
    r'giao hàng nhanh.*\bjt\s+express\b',
    r'\bvnpost\b.*giao hàng nhanh',
    r'giao hàng nhanh.*\bvnpost\b',
    r'ninja van.*giao hàng nhanh',
    r'giao hàng nhanh.*ninja van',
    r'best express.*giao hàng nhanh',
    r'giao hàng nhanh.*best express',
    r'\bspx\b.*giao hàng nhanh',
    r'giao hàng nhanh.*\bspx\b',
    r'đấu giá.*\bghn\b',
    r'đấu giá.*giao hàng nhanh',
    r'phiên đấu giá.*\bghn\b',
    r'phiên đấu giá.*giao hàng nhanh',
    r'\bship\s+(các\s+)?tỉnh\b',
    r'\bship\s+liên\s+tỉnh\b',
    r'gas (south|xanh|chính hãng).*\d{3}\.\d{3}',
    r'bình\s+\d{1,3}\s*kg.*\d{3}\.\d{3}',
    r'gas south pvn',
    r'phúc lộc thọ gas',
    r'tấm ốp nano hd',
    r'phào chỉ pu',
    r'băng quấn chống ăn mòn',
    r'khô cá lóc.*nắng',
    r'cá lóc.*1 nắng',
    r'phở cuốn.*giao',
    r'gửi hàng đi (mỹ|úc|hàn|nhật|sing|canada|đức)',
    r'chuyển hàng (đi|về|từ)?\s*(mỹ|úc|usa|aus|nhật|hàn|nước ngoài)',
    r'dịch vụ chuyển hàng quốc tế',
    r'vận chuyển (hàng hóa )?(mỹ|úc|quốc tế).*việt',
    r'#vậnchuyển(mỹviệt|quốctế|hànghóa)',
    r'mother.?s day.*(mẹ ở (úc|mỹ|hàn|nhật)|gửi.*mẹ)',
    r'kho nệm',
    r'\bnệm pu\b',
    r'feedback.*nệm',
    r'giao nước (tận nhà|đến nhà|miễn phí|tại nhà)',
    r'đại lý nước (uống|suối|tinh khiết|lavie|aquafina)',
    r'nước uống.*đóng bình',
    r'\bđấu giá\b.*(giá khởi điểm|bước giá|bid|kết thúc.*\d+h)',
    r'giá khởi điểm.*\d+k',
    r'bước giá.*\d+k',
    r'phiên đấu giá',
    r'phớt thủy lực',
    r'gioăng phớt',
    r'gioangphot\.com',
    r'phớt vintin',
    r'phớt nok',
    r'mực (khô|một nắng).*ngon',
    r'mực siêu (to|dày|chất)',
    r'mực\s+khô\s+vintin',
    r'bàn ghế ăn.*nhập khẩu',
    r'bàn đá ceramic',
    r'ghế da xương cá',
    r'noithatnhabepnhapkhau|banangiare|nội thất nhà bếp nhập khẩu',
    r'hỏa tốc 247|hoả tốc 247',
    r'\bship\s+hỏa\s+tốc\b|\bship\s+hoả\s+tốc\b',
    r'app hỏa tốc|ứng dụng hỏa tốc|hỏa tốc.*ứng dụng',
    r'xe tải van.*thaco',
]


# ============== Brand-discussion / multi-carrier safe-harbor ==============
GHN_MENTION_PATTERN = r'\b(ghn|giao hàng nhanh)\b'

DISCUSSION_PATTERN = (
    r'\b(khiếu nại|phàn nàn|than\s|ớn\b|sợ\b|ngán|ngại|tệ\b|kém\b|chậm\b|xuống cấp'
    r'|chết\s+(dưới|tay)|mất\s+(hàng|đơn)|hoàn\s+(tiền|hàng)|đền|bồi thường'
    r'|không\s+(giao|lấy|nhận|trả|thèm)|hỗ trợ\s+kém|dvkh|app\s+(dễ|khó)'
    r'|dối trá|lừa|gian lận|\breview\b|so sánh|trải nghiệm|kinh nghiệm'
    r'|cá nhân.*thấy|tôi\s+(sang|chuyển|dùng|đặt|gửi|ship|tạo|tạm|chọn)'
    r'|gửi qua|ship qua|đơn\s+(điều phối|hoàn|lộn nhộn|đi|đến|ghn|ghtk|spx|jt|viettel)'
    r'|cũng\s+(tạm|ổn|ok)|thấy\s+(ok|ổn|tệ|kém|jt|spx|ghn)'
    r'|tăng\s+giá|giục\s+đơn|giao\s+đơn\s+(thành công|chậm|lộn)|giao\s+chậm|chậm\s+trễ'
    r'|cập\s+nhật\s+giao\s+đơn|chốt\s+đơn\s+không\s+lấy|không\s+được\s+duyệt'
    r'|bưu\s+điện|chuyển\s+sang|sang\s+(tạm|dùng|thử)|trc\s+\w+\s+quá\s+là\s+ok'
    r'|nchung|tới lui|bóc\s+phốt|\bphốt\b|\btróng\b|hư\s+hỏng)\b'
)

CARRIER_LIST_PATTERN = (
    r'\b(ghn|giao hàng nhanh|ghtk|giao hàng tiết kiệm|spx|shopee\s*express'
    r'|j\s*&\s*t|jt\s+express|jt\b|viettel\s*post|viettelpost|vnpost|vnp\b'
    r'|ninja\s*van|best\s*express|ems\b|grab\s*express|lalamove|ahamove|nhất tín)\b'
)


# ── COMPILE REGEX (one-time) ─────────────────────────────────────────────────
def _compile():
    return {
        'whitelist':     re.compile('|'.join(f'(?:{p})' for p in GHN_COMMUNITY_WHITELIST), re.IGNORECASE),
        'brand':         re.compile('|'.join(f'(?:{p})' for p in GHN_BRAND_STRONG), re.IGNORECASE),
        'product':       re.compile(PRODUCT_CATEGORIES, re.IGNORECASE),
        'price':         re.compile(PRICE_PATTERNS, re.IGNORECASE),
        'contact':       re.compile(CONTACT_PATTERNS, re.IGNORECASE),
        'emoji':         re.compile(EMOJI_MARKERS),
        'cta':           re.compile(CTA_DESCRIPTOR_GHN, re.IGNORECASE),
        'spam_site':     re.compile('|'.join(f'(?:{p})' for p in SPAM_SITE_PATTERNS), re.IGNORECASE),
        'spam_content':  re.compile('|'.join(f'(?:{p})' for p in SPAM_CONTENT_PATTERNS), re.IGNORECASE),
        'personal':      re.compile(r'[a-z0-9._\-]{4,40}'),
        'ship_cta':      re.compile(
            r'\bship\s+(nhanh|toàn quốc|tận (nhà|nơi|tay)|miễn phí|tỉnh|liên tỉnh)\b'
            r'|\bgiao\s+(ngay|nhanh|trong ngày|2h|siêu tốc|hỏa tốc)\b',
            re.IGNORECASE),
        'ghn_phrase':    re.compile(r'giao hàng nhanh', re.IGNORECASE),
        'ghn_mention':   re.compile(GHN_MENTION_PATTERN, re.IGNORECASE),
        'discussion':    re.compile(DISCUSSION_PATTERN, re.IGNORECASE),
        'carrier_list':  re.compile(CARRIER_LIST_PATTERN, re.IGNORECASE),
    }


_REGEX = _compile()


def _count_carriers(text: str) -> int:
    """Dem so don vi van chuyen distinct duoc nhac den trong text."""
    found = set()
    for m in _REGEX['carrier_list'].finditer(text):
        s = re.sub(r'\s+', ' ', m.group(0).lower().strip())
        s = s.replace(' & ', '&').replace(' &', '&').replace('& ', '&')
        if s in ('giao hàng nhanh', 'ghn'):
            s = 'ghn'
        elif s in ('giao hàng tiết kiệm', 'ghtk'):
            s = 'ghtk'
        elif s in ('shopee express', 'spx'):
            s = 'spx'
        elif s in ('jt express', 'jt', 'j&t'):
            s = 'jt'
        elif s in ('viettel post', 'viettelpost'):
            s = 'viettelpost'
        elif s in ('vnp', 'vnpost'):
            s = 'vnpost'
        elif s == 'grab express':
            s = 'grab'
        found.add(s)
    return len(found)


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _first_match(pattern_re: re.Pattern, text: str) -> Optional[str]:
    """Trả về chuỗi khớp đầu tiên, hoặc None."""
    m = pattern_re.search(text)
    return m.group(0) if m else None


def _first_site_match(text: str) -> Optional[str]:
    """Trả về pattern site spam đầu tiên khớp."""
    for p in SPAM_SITE_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def _first_content_match(text: str) -> Optional[str]:
    """Trả về pattern content spam đầu tiên khớp."""
    for p in SPAM_CONTENT_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


# ── MAIN CLASSIFIER ──────────────────────────────────────────────────────────

def classify_ghn_custom(
    title: Optional[str],
    content: Optional[str],
    description: Optional[str],
    site_name: Optional[str] = None,
) -> dict:
    """
    Phan loai spam cho cac index GHN.

    Returns:
        {
            "is_spam"      : bool,
            "reason"       : str,          # layer/label kích hoạt
            "matched_rules": list[str],    # các signal/pattern thực sự khớp
        }
    """
    title       = (title or "").strip()
    content     = (content or "").strip()
    description = (description or "").strip()
    site        = (site_name or "").strip().lower()

    full = f"{title} {content} {description}".lower()

    # L0: whitelist site (cong dong GHN)
    if site and _REGEX['whitelist'].search(site):
        wl_match = _first_match(_REGEX['whitelist'], site)
        return {
            "is_spam": False,
            "reason": "ghn_community_whitelist",
            "matched_rules": [f"whitelist_site:{wl_match}"],
        }

    has_brand   = bool(_REGEX['brand'].search(full))
    has_emoji   = bool(_REGEX['emoji'].search(full))
    has_price   = bool(_REGEX['price'].search(full))
    has_contact = bool(_REGEX['contact'].search(full))
    has_product = bool(_REGEX['product'].search(full))
    has_cta     = bool(_REGEX['cta'].search(full))

    score = 0
    signals: list[str] = []
    if has_emoji:
        score += 1
        signals.append(f"emoji:{_first_match(_REGEX['emoji'], full)}")
    if has_price:
        score += 1
        signals.append(f"price:{_first_match(_REGEX['price'], full)}")
    if has_contact:
        score += 1
        signals.append(f"contact:{_first_match(_REGEX['contact'], full)}")
    if has_product:
        score += 2
        signals.append(f"product:{_first_match(_REGEX['product'], full)}")
    if has_cta:
        score += 2
        signals.append(f"cta:{_first_match(_REGEX['cta'], full)}")

    # Brand-Discussion Safe-Harbor (kich hoat khi score < 5)
    if score < 5:
        has_ghn_mention = bool(_REGEX['ghn_mention'].search(full))
        has_discuss     = bool(_REGEX['discussion'].search(full))
        n_carriers      = _count_carriers(full)
        if (has_ghn_mention and has_discuss) or n_carriers >= 2:
            discuss_match = _first_match(_REGEX['discussion'], full)
            return {
                "is_spam": False,
                "reason": "ghn_brand_discussion",
                "matched_rules": [
                    f"ghn_mention:{has_ghn_mention}",
                    f"discussion:{discuss_match}",
                    f"carriers:{n_carriers}",
                ],
            }

    # L1: strong sales score + khong brand → Rac
    if score >= 3 and not has_brand:
        return {
            "is_spam": True,
            "reason": "ghn_spam_sales_score",
            "matched_rules": signals + [f"score:{score}"],
        }

    if site and _REGEX['personal'].fullmatch(site) and has_product and not has_brand:
        return {
            "is_spam": True,
            "reason": "ghn_spam_personal_site_product",
            "matched_rules": [f"personal_site:{site}"] + signals,
        }

    # L1.5: Brand strong safe-harbor som
    if has_brand:
        brand_match = _first_match(_REGEX['brand'], full)
        if site and _REGEX['spam_site'].search(site):
            site_match = _first_site_match(site)
            return {
                "is_spam": True,
                "reason": "ghn_spam_brand_on_spam_site",
                "matched_rules": [f"brand:{brand_match}", f"spam_site:{site_match}"],
            }
        return {
            "is_spam": False,
            "reason": "ghn_brand_strong",
            "matched_rules": [f"brand:{brand_match}"],
        }

    # L2: site spam
    if site and _REGEX['spam_site'].search(site):
        site_match = _first_site_match(site)
        return {
            "is_spam": True,
            "reason": "ghn_spam_site",
            "matched_rules": [f"spam_site:{site_match}"],
        }

    # L3: spam content
    content_match = _first_content_match(full)
    if content_match:
        return {
            "is_spam": True,
            "reason": "ghn_spam_content",
            "matched_rules": [f"spam_content:{content_match}"],
        }

    # L3.5: "giao hang nhanh" + sales signal ma khong co brand → Rac
    if _REGEX['ghn_phrase'].search(full):
        if has_price or has_contact or has_product or has_cta or score >= 2:
            return {
                "is_spam": True,
                "reason": "ghn_spam_phrase_with_sales",
                "matched_rules": ["trigger:giao_hang_nhanh"] + signals,
            }

    # L5: (contact/price) + product
    if (has_contact or has_price) and has_product:
        return {
            "is_spam": True,
            "reason": "ghn_spam_contact_price_product",
            "matched_rules": signals,
        }

    # L6: cta + product/price
    if has_cta and (has_product or has_price):
        return {
            "is_spam": True,
            "reason": "ghn_spam_cta_product",
            "matched_rules": signals,
        }

    # L7: ship CTA manh
    ship_match = _first_match(_REGEX['ship_cta'], full)
    if ship_match:
        return {
            "is_spam": True,
            "reason": "ghn_spam_ship_cta",
            "matched_rules": [f"ship_cta:{ship_match}"],
        }

    return {"is_spam": False, "reason": "ghn_no_match", "matched_rules": []}
