#!/usr/bin/env python3
"""
Test cases for different spam scenarios
"""
import asyncio
import httpx
import json

# Test cases for different spam types
test_cases = [
    {
        "name": "Legitimate Finance Question (NOT SPAM)",
        "data": {
            "id": "1",
            "index": "idx_1",
            "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà?",
            "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn?",
            "type": "tiktokComment",
            "category": "Finance"
        }
    },
    {
        "name": "Commercial Spam (SPAM)",
        "data": {
            "id": "2", 
            "index": "idx_2",
            "title": "Bán hàng online",
            "content": "Bán áo thun giá rẻ chỉ 99k, inbox mua ngay! Liên hệ 0123456789",
            "type": "fbPageComment",
            "category": "Consumer Discretionary"
        }
    },
    {
        "name": "Font Error Spam (SPAM)",
        "data": {
            "id": "3",
            "index": "idx_3", 
            "title": "Thảo luận công nghệ",
            "content": "t0i mu0n mua đi3n th0ai m0i, c0 ai bi3t ch0 nao ban kh0ng?",
            "type": "forumComment",
            "category": "Information Tech"
        }
    },
    {
        "name": "Abbreviation Spam (SPAM)",
        "data": {
            "id": "4",
            "index": "idx_4",
            "title": "Chat group",
            "content": "e cần mua đt mới, ai bt chỗ nào bán rẻ k? inbox e nha, tks all",
            "type": "fbGroupComment", 
            "category": "Information Tech"
        }
    },
    {
        "name": "Real Estate Ad (NOT SPAM)",
        "data": {
            "id": "5",
            "index": "idx_5",
            "title": "Bán nhà đất",
            "content": "Bán lô đất 100m2 tại Hà Nội, giá 2 tỷ, sổ đỏ chính chủ. LH: 0987654321",
            "type": "fbPageComment",
            "category": "Real Estate"
        }
    },
    {
        "name": "Suspicious Link Spam (SPAM)",
        "data": {
            "id": "6",
            "index": "idx_6",
            "title": "Kiếm tiền online",
            "content": "Kiếm tiền dễ dàng tại nhà, click link: bit.ly/xxx để biết thêm chi tiết",
            "type": "youtubeComment",
            "category": "Finance"
        }
    }
]

async def test_spam_detection():
    """Test various spam detection scenarios"""
    async with httpx.AsyncClient() as client:
        print("Testing Spam Detection Cases...\n")
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                print(f"{i}. {test_case['name']}")
                print(f"Content: {test_case['data']['content'][:50]}...")
                
                response = await client.post(
                    "http://localhost:8000/detect-spam",
                    json=test_case['data'],
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    spam_status = "SPAM" if result['is_spam'] else "NOT SPAM"
                    print(f"Result: {spam_status}")
                else:
                    print(f"Error: {response.status_code}")
                    
            except Exception as e:
                print(f"Error: {e}")
            
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_spam_detection())