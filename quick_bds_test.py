#!/usr/bin/env python3
"""
Quick test cho case BĐS từ curl request
"""

import requests
import json

def test_bds_finance_case():
    """Test case tài chính BĐS từ curl của bạn"""
    
    url = "http://localhost:8010/detect-spam"  # Thay đổi IP nếu cần
    
    # Data từ curl request của bạn
    data = {
        "id": "10238500853796158_1439407534649725",
        "index": "5cf117c8f2bff1e200c7d49b", 
        "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ?  #congtytaichinh #fecredit #homecredit #vaytienonline",
        "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn? ",
        "description": "",
        "type": "tiktokComment", 
        "category": "Finance"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing BĐS Finance Case")
    print("=" * 40)
    print(f"📝 Title: {data['title']}")
    print(f"💬 Content: {data['content'][:80]}...")
    print(f"🏷️  Category: {data['category']}")
    print(f"📂 Type: {data['type']}")
    print()
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Response received:")
            print(f"   ID: {result['id']}")
            print(f"   Type: {result['type']}")
            print(f"   Is Spam: {result['is_spam']}")
            print(f"   Result: {'SPAM' if result['is_spam'] else 'NOT_SPAM'}")
            print()
            
            # Analysis
            if result['is_spam']:
                print("❌ PHÂN TÍCH: Hệ thống đánh giá là SPAM")
                print("💡 Lý do có thể:")
                print("   - Có từ khóa 'nợ', 'bùng' có thể bị hiểu nhầm")
                print("   - Nội dung về tài chính có thể bị coi là nhạy cảm")
            else:
                print("✅ PHÂN TÍCH: Hệ thống đánh giá là NOT_SPAM")
                print("💡 Lý do:")
                print("   - Đây là hỏi đáp về tài chính (Finance category)")
                print("   - Không có SĐT, link, quảng cáo")
                print("   - Nội dung thảo luận bình thường")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Kiểm tra:")
        print("   - API có đang chạy không?")
        print("   - URL có đúng không?")
        print("   - Network connection")

def test_multiple_bds_cases():
    """Test nhiều case BĐS khác nhau"""
    
    url = "http://localhost:8010/detect-spam"
    
    test_cases = [
        {
            "name": "Finance Comment (Original)",
            "data": {
                "id": "finance_001",
                "index": "idx_001",
                "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ?",
                "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn?",
                "description": "",
                "type": "tiktokComment",
                "category": "Finance"
            },
            "expected": "NOT_SPAM"
        },
        {
            "name": "BĐS Rao vặt có SĐT",
            "data": {
                "id": "bds_001",
                "index": "idx_002", 
                "title": "Bán nhà 3 tầng giá rẻ",
                "content": "Bán nhà đẹp 3 tầng, giá chỉ 2.5 tỷ. Liên hệ: 0123456789",
                "description": "Rao vặt BĐS",
                "type": "fbGroupTopic",
                "category": "Real Estate"
            },
            "expected": "SPAM"
        },
        {
            "name": "Thảo luận BĐS bình thường",
            "data": {
                "id": "bds_002",
                "index": "idx_003",
                "title": "Thị trường BĐS hiện tại",
                "content": "Mọi người nghĩ sao về thị trường bất động sản hiện tại? Có nên mua nhà không?",
                "description": "Thảo luận BĐS", 
                "type": "forumTopic",
                "category": "Real Estate"
            },
            "expected": "NOT_SPAM"
        }
    ]
    
    print("\n🏠 Testing Multiple BĐS Cases")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {case['name']}")
        print(f"Expected: {case['expected']}")
        
        try:
            response = requests.post(url, json=case['data'], timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                actual = "SPAM" if result['is_spam'] else "NOT_SPAM"
                
                if actual == case['expected']:
                    print(f"✅ PASS: {actual}")
                else:
                    print(f"❌ FAIL: Got {actual}, Expected {case['expected']}")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test case gốc từ curl
    test_bds_finance_case()
    
    # Test thêm các case khác
    test_multiple_bds_cases()