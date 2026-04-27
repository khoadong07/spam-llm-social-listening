#!/usr/bin/env python3
"""
Test cases cho Bất Động Sản (Real Estate)
"""

import asyncio
import aiohttp
import json


async def test_bds_cases():
    """Test các case BĐS khác nhau"""
    
    base_url = "http://localhost:8010"  # Thay đổi URL nếu cần
    
    # Test cases cho BĐS
    bds_test_cases = [
        {
            "name": "Finance Comment - Nợ tài chính (NOT_SPAM)",
            "data": {
                "id": "10238500853796158_1439407534649725",
                "index": "5cf117c8f2bff1e200c7d49b",
                "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ?  #congtytaichinh #fecredit #homecredit #vaytienonline",
                "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn?",
                "description": "",
                "type": "tiktokComment",
                "category": "Finance"
            },
            "expected": False  # NOT_SPAM - hỏi đáp về tài chính
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
            "expected": False  # NOT_SPAM - thảo luận BĐS đúng category
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
            "expected": True  # SPAM - có SĐT, quảng cáo bán hàng
        },
        {
            "name": "BĐS sai category - Rao BĐS trong group công nghệ (SPAM)",
            "data": {
                "id": "bds_wrong_cat_001",
                "index": "bds_wrong_cat_idx_001",
                "title": "Bán căn hộ chung cư cao cấp",
                "content": "Bán căn hộ 2PN, 2WC, view đẹp, giá 3.5 tỷ. Liên hệ em để xem nhà.",
                "description": "Bán căn hộ",
                "type": "fbGroupTopic",
                "category": "Information Tech"  # Sai category - BĐS trong group IT
            },
            "expected": True  # SPAM - BĐS sai category
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
            "expected": False  # NOT_SPAM - hỏi đáp tư vấn
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
            "expected": True  # SPAM - có link, quảng cáo dịch vụ
        },
        {
            "name": "Review dự án BĐS (NOT_SPAM)",
            "data": {
                "id": "bds_review_001",
                "index": "bds_review_idx_001",
                "title": "Review dự án Vinhomes Grand Park",
                "content": "Mình đã sống ở đây 1 năm, chia sẻ trải nghiệm thực tế về tiện ích, giao thông, môi trường sống.",
                "description": "Review dự án BĐS",
                "type": "forumTopic",
                "category": "Real Estate"
            },
            "expected": False  # NOT_SPAM - review, chia sẻ kinh nghiệm
        },
        {
            "name": "Tuyển dụng BĐS sai category (SPAM)",
            "data": {
                "id": "bds_job_001",
                "index": "bds_job_idx_001",
                "title": "Tuyển nhân viên kinh doanh BĐS",
                "content": "Công ty tuyển nhân viên bán hàng BĐS, lương cao, hoa hồng hấp dẫn. Liên hệ HR: 0987654321",
                "description": "Tuyển dụng",
                "type": "fbGroupTopic",
                "category": "Information Tech"  # Sai category - tuyển dụng BĐS trong group IT
            },
            "expected": True  # SPAM - tuyển dụng sai category
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        print("🏠 TESTING BẤT ĐỘNG SẢN (REAL ESTATE) CASES")
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
        
        # Test từng case
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
                        
                        # Show content for failed tests
                        if actual_spam != expected_spam:
                            print(f"   📝 Content: {test_case['data']['content'][:100]}...")
                            print(f"   🏷️  Category: {test_case['data']['category']}")
                            print(f"   📂 Type: {test_case['data']['type']}")
                    else:
                        print(f"   ❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed. Check the logic for BĐS cases.")


async def test_single_bds_case():
    """Test case đơn lẻ như trong curl request của bạn"""
    
    base_url = "http://localhost:8010"
    
    # Case từ curl request của bạn
    test_data = {
        "id": "10238500853796158_1439407534649725",
        "index": "5cf117c8f2bff1e200c7d49b",
        "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ?  #congtytaichinh #fecredit #homecredit #vaytienonline",
        "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn? ",
        "description": "",
        "type": "tiktokComment",
        "category": "Finance"
    }
    
    async with aiohttp.ClientSession() as session:
        print("🧪 TESTING SINGLE BĐS CASE (From your curl)")
        print("=" * 50)
        
        try:
            async with session.post(
                f"{base_url}/detect-spam",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"📋 Test Case: Finance Comment về nợ tài chính")
                    print(f"📝 Content: {test_data['content'][:100]}...")
                    print(f"🏷️  Category: {test_data['category']}")
                    print(f"📂 Type: {test_data['type']}")
                    print(f"🎯 Result: {'SPAM' if result['is_spam'] else 'NOT_SPAM'}")
                    print(f"💡 Expected: NOT_SPAM (hỏi đáp về tài chính)")
                    
                    if not result['is_spam']:
                        print("✅ CORRECT: Đây là hỏi đáp về tài chính, không phải spam")
                    else:
                        print("❌ INCORRECT: Hệ thống đánh giá sai, đây không phải spam")
                        
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")


if __name__ == "__main__":
    print("Chọn test mode:")
    print("1. Test tất cả BĐS cases")
    print("2. Test single case (từ curl của bạn)")
    
    choice = input("Nhập lựa chọn (1 hoặc 2): ").strip()
    
    if choice == "1":
        asyncio.run(test_bds_cases())
    elif choice == "2":
        asyncio.run(test_single_bds_case())
    else:
        print("Chạy cả 2 tests...")
        asyncio.run(test_single_bds_case())
        print("\n" + "="*60 + "\n")
        asyncio.run(test_bds_cases())