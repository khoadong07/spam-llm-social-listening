#!/usr/bin/env python3
"""
Clear cache và test lại BĐS cases với prompt mới
"""

import asyncio
import aiohttp
import redis.asyncio as redis


async def clear_cache():
    """Clear Redis cache"""
    try:
        redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        
        # Get all spam cache keys
        keys = await redis_client.keys("spam_cache:*")
        if keys:
            deleted = await redis_client.delete(*keys)
            print(f"🗑️  Cleared {deleted} cache entries")
        else:
            print("🗑️  No cache entries to clear")
            
        await redis_client.close()
        
    except Exception as e:
        print(f"❌ Cache clear error: {e}")


async def test_failed_cases():
    """Test lại 2 cases đã failed"""
    
    base_url = "http://localhost:8010"
    
    failed_cases = [
        {
            "name": "Real Estate Spam - Rao vặt BĐS có SĐT (Should be SPAM)",
            "data": {
                "id": "bds_spam_001",
                "index": "bds_spam_idx_001",
                "title": "BÁN NHÀ GIÁ RẺ - LIÊN HỆ NGAY",
                "content": "Bán nhà 3 tầng giá chỉ 2 tỷ, vị trí đẹp, gần trường học. Liên hệ: 0123456789 hoặc Zalo để xem nhà ngay!",
                "description": "Rao vặt bán nhà",
                "type": "fbGroupTopic",
                "category": "Real Estate"
            },
            "expected": True  # SPAM
        },
        {
            "name": "Môi giới BĐS có link (Should be SPAM)",
            "data": {
                "id": "bds_broker_001",
                "index": "bds_broker_idx_001",
                "title": "Nhận ký gửi mua bán BĐS",
                "content": "Công ty chúng tôi chuyên mua bán, cho thuê BĐS. Hoa hồng cao, thủ tục nhanh. Xem thêm: https://example.com/bds",
                "description": "Dịch vụ môi giới",
                "type": "fbGroupTopic",
                "category": "Real Estate"
            },
            "expected": True  # SPAM
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🧪 TESTING FAILED BĐS CASES WITH NEW PROMPT")
        print("=" * 60)
        
        # Health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status != 200:
                    print("❌ API không hoạt động!")
                    return
            print("✅ API đang hoạt động!")
        except:
            print("❌ Không thể kết nối tới API!")
            return
        
        for i, case in enumerate(failed_cases, 1):
            print(f"\n📋 Test {i}: {case['name']}")
            
            try:
                async with session.post(
                    f"{base_url}/detect-spam",
                    json=case['data'],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        actual_spam = result['is_spam']
                        expected_spam = case['expected']
                        
                        print(f"📝 Content: {case['data']['content'][:80]}...")
                        print(f"🏷️  Category: {case['data']['category']}")
                        print(f"📂 Type: {case['data']['type']}")
                        
                        if actual_spam == expected_spam:
                            status = "✅ PASS"
                        else:
                            status = "❌ STILL FAIL"
                        
                        spam_text = "SPAM" if actual_spam else "NOT_SPAM"
                        expected_text = "SPAM" if expected_spam else "NOT_SPAM"
                        
                        print(f"🎯 Result: {spam_text} | Expected: {expected_text} | {status}")
                        
                        # Analysis
                        if actual_spam == expected_spam:
                            print("💡 Prompt cải thiện đã hoạt động!")
                        else:
                            print("💡 Cần cải thiện thêm prompt hoặc logic")
                            
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Exception: {e}")


async def test_all_bds_cases():
    """Test lại tất cả BĐS cases"""
    
    base_url = "http://localhost:8010"
    
    bds_test_cases = [
        {
            "name": "Finance Comment - Nợ tài chính (NOT_SPAM)",
            "data": {
                "id": "10238500853796158_1439407534649725",
                "index": "5cf117c8f2bff1e200c7d49b",
                "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ?",
                "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn?",
                "description": "",
                "type": "tiktokComment",
                "category": "Finance"
            },
            "expected": False
        },
        {
            "name": "Real Estate Topic - Thảo luận BĐS đúng ngữ cảnh (NOT_SPAM)",
            "data": {
                "id": "bds_001",
                "index": "bds_idx_001",
                "title": "Thị trường BĐS hiện tại như thế nào?",
                "content": "Mọi người cho em hỏi thị trường bất động sản hiện tại có nên đầu tư không? Giá nhà đất có xu hướng tăng hay giảm?",
                "description": "Thảo luận về thị trường BĐS",
                "type": "forumTopic",
                "category": "Real Estate"
            },
            "expected": False
        },
        {
            "name": "Real Estate Spam - Rao vặt BĐS có SĐT (SPAM)",
            "data": {
                "id": "bds_spam_001",
                "index": "bds_spam_idx_001",
                "title": "BÁN NHÀ GIÁ RẺ - LIÊN HỆ NGAY",
                "content": "Bán nhà 3 tầng giá chỉ 2 tỷ, vị trí đẹp, gần trường học. Liên hệ: 0123456789 hoặc Zalo để xem nhà ngay!",
                "description": "Rao vặt bán nhà",
                "type": "fbGroupTopic",
                "category": "Real Estate"
            },
            "expected": True
        },
        {
            "name": "Môi giới BĐS có link (SPAM)",
            "data": {
                "id": "bds_broker_001",
                "index": "bds_broker_idx_001",
                "title": "Nhận ký gửi mua bán BĐS",
                "content": "Công ty chúng tôi chuyên mua bán, cho thuê BĐS. Hoa hồng cao, thủ tục nhanh. Xem thêm: https://example.com/bds",
                "description": "Dịch vụ môi giới",
                "type": "fbGroupTopic",
                "category": "Real Estate"
            },
            "expected": True
        },
        {
            "name": "Tư vấn mua nhà - Hỏi đáp (NOT_SPAM)",
            "data": {
                "id": "bds_advice_001",
                "index": "bds_advice_idx_001",
                "title": "Tư vấn mua nhà lần đầu",
                "content": "Em mới ra trường, muốn mua nhà nhưng chưa có kinh nghiệm. Mọi người tư vấn em nên chú ý những gì khi mua nhà?",
                "description": "Xin tư vấn mua nhà",
                "type": "forumTopic",
                "category": "Real Estate"
            },
            "expected": False
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print(f"\n🏠 TESTING ALL BĐS CASES WITH IMPROVED PROMPT")
        print("=" * 60)
        
        total_tests = len(bds_test_cases)
        passed_tests = 0
        
        for i, test_case in enumerate(bds_test_cases, 1):
            print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
            
            try:
                async with session.post(
                    f"{base_url}/detect-spam",
                    json=test_case['data'],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        actual_spam = result['is_spam']
                        expected_spam = test_case['expected']
                        
                        if actual_spam == expected_spam:
                            status = "✅ PASS"
                            passed_tests += 1
                        else:
                            status = "❌ FAIL"
                        
                        spam_text = "SPAM" if actual_spam else "NOT_SPAM"
                        expected_text = "SPAM" if expected_spam else "NOT_SPAM"
                        
                        print(f"   Result: {spam_text} | Expected: {expected_text} | {status}")
                        
                    else:
                        print(f"   ❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 IMPROVED PROMPT RESULTS")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Prompt improvement successful!")
        elif passed_tests > 3:  # Previous was 6/8
            print("✅ IMPROVEMENT! Better than before!")
        else:
            print("⚠️  Need more prompt tuning...")


async def main():
    """Main function"""
    print("🔄 CLEARING CACHE AND RETESTING BĐS CASES")
    print("=" * 60)
    
    # Clear cache first
    await clear_cache()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Test failed cases first
    await test_failed_cases()
    
    # Test all cases
    await test_all_bds_cases()


if __name__ == "__main__":
    asyncio.run(main())