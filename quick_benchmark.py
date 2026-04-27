#!/usr/bin/env python3
"""
Quick benchmark test - Test đơn giản để kiểm tra tốc độ API
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime


async def quick_test():
    """Test nhanh với 100 requests đồng thời"""
    
    # Sample data
    test_data = {
        "id": "test_001",
        "index": "idx_001", 
        "title": "Hỏi về sản phẩm công nghệ",
        "content": "Mọi người cho em hỏi về laptop gaming tầm 20 triệu có gì tốt không ạ?",
        "description": "Tư vấn mua laptop",
        "type": "forumTopic",
        "category": "Information Tech"
    }
    
    # Test newsTopic bypass
    news_data = {
        "id": "news_001",
        "index": "idx_news_001",
        "title": "Tin tức công nghệ",
        "content": "Apple ra mắt sản phẩm mới",
        "description": "Tin tức",
        "type": "newsTopic",
        "category": "Information Tech"
    }
    
    base_url = "http://localhost:8010"
    
    async with aiohttp.ClientSession() as session:
        # Health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status != 200:
                    print("❌ API không hoạt động!")
                    return
        except:
            print("❌ Không thể kết nối tới API!")
            return
        
        print("✅ API đang hoạt động!")
        
        # Test newsTopic bypass
        print("\n🧪 Testing newsTopic bypass...")
        start = time.time()
        async with session.post(f"{base_url}/detect-spam", json=news_data) as response:
            if response.status == 200:
                result = await response.json()
                bypass_time = time.time() - start
                print(f"✅ newsTopic bypass: is_spam={result['is_spam']}, time={bypass_time*1000:.2f}ms")
            else:
                print("❌ newsTopic test failed")
        
        # Test concurrent requests
        print(f"\n🚀 Testing 100 concurrent requests...")
        
        async def single_request(session, data, req_id):
            try:
                data_copy = data.copy()
                data_copy["id"] = f"test_{req_id}"
                data_copy["index"] = f"idx_{req_id}"
                
                start = time.time()
                async with session.post(f"{base_url}/detect-spam", json=data_copy) as response:
                    duration = time.time() - start
                    if response.status == 200:
                        return True, duration
                    else:
                        return False, duration
            except:
                return False, time.time() - start
        
        # Run 100 concurrent requests
        start_time = time.time()
        tasks = [single_request(session, test_data, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for success, _ in results if success)
        failed = len(results) - successful
        response_times = [duration for _, duration in results]
        avg_response_time = sum(response_times) / len(response_times)
        
        print(f"\n📊 RESULTS:")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"✅ Successful: {successful}/100")
        print(f"❌ Failed: {failed}/100")
        print(f"🚀 Requests/second: {successful/total_time:.2f}")
        print(f"⚡ Avg response time: {avg_response_time*1000:.2f}ms")
        print(f"📈 Estimated max RPS: {100/total_time:.2f}")
        print(f"📊 Requests per minute: {(100/total_time)*60:.0f}")
        
        # Test cache performance
        print(f"\n💾 Testing cache performance...")
        cache_test_data = test_data.copy()
        cache_test_data["id"] = "cache_test"
        cache_test_data["index"] = "cache_idx"
        
        # First request (no cache)
        start = time.time()
        async with session.post(f"{base_url}/detect-spam", json=cache_test_data) as response:
            first_time = time.time() - start
            if response.status == 200:
                print(f"🔥 First request (no cache): {first_time*1000:.2f}ms")
        
        # Second request (should hit cache)
        start = time.time()
        async with session.post(f"{base_url}/detect-spam", json=cache_test_data) as response:
            second_time = time.time() - start
            if response.status == 200:
                print(f"⚡ Second request (cache hit): {second_time*1000:.2f}ms")
                speedup = first_time / second_time if second_time > 0 else 0
                print(f"🚀 Cache speedup: {speedup:.2f}x faster")


if __name__ == "__main__":
    print("🔥 QUICK SPAM DETECTION BENCHMARK")
    print("=" * 50)
    asyncio.run(quick_test())