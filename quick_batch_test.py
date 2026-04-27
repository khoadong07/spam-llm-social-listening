#!/usr/bin/env python3
"""
Quick batch size test - Test nhanh các batch size phổ biến
"""

import asyncio
import aiohttp
import time
import json


async def test_batch_performance():
    """Test performance của các batch size khác nhau"""
    
    base_url = "http://localhost:8010"
    
    # Test data - mix of different types for realistic testing
    def generate_batch_data(size):
        data = []
        for i in range(size):
            if i % 4 == 0:  # 25% newsTopic (instant)
                item = {
                    "id": f"news_{i}",
                    "index": f"idx_{i}",
                    "title": "Tin tức công nghệ mới",
                    "content": f"Tin tức số {i} về công nghệ",
                    "description": "Tin tức",
                    "type": "newsTopic",
                    "category": "Information Tech"
                }
            elif i % 4 == 1:  # 25% cache hits
                item = {
                    "id": f"cache_{i}",
                    "index": f"idx_{i}",
                    "title": "Hỏi về laptop gaming",
                    "content": "Mọi người tư vấn laptop gaming tầm 20 triệu",
                    "description": "Tư vấn",
                    "type": "forumTopic", 
                    "category": "Information Tech"
                }
            elif i % 4 == 2:  # 25% finance discussion
                item = {
                    "id": f"finance_{i}",
                    "index": f"idx_{i}",
                    "title": "Thảo luận tài chính",
                    "content": "Mọi người nghĩ sao về đầu tư chứng khoán?",
                    "description": "Thảo luận",
                    "type": "forumTopic",
                    "category": "Finance"
                }
            else:  # 25% new content (LLM calls)
                item = {
                    "id": f"new_{i}",
                    "index": f"idx_{i}",
                    "title": f"Nội dung mới {i}",
                    "content": f"Đây là nội dung hoàn toàn mới số {i} để test",
                    "description": "Nội dung mới",
                    "type": "forumTopic",
                    "category": "Consumer Discretionary"
                }
            data.append(item)
        return data
    
    # Test different batch sizes
    batch_sizes = [1, 5, 10, 20, 30, 50, 75, 100]
    
    async with aiohttp.ClientSession() as session:
        print("🧪 QUICK BATCH SIZE PERFORMANCE TEST")
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
        
        print(f"\n{'Size':>4} | {'Time':>6} | {'Items/s':>8} | {'Status'}")
        print(f"{'-'*4}-+-{'-'*6}-+-{'-'*8}-+-{'-'*10}")
        
        results = []
        
        for batch_size in batch_sizes:
            test_data = generate_batch_data(batch_size)
            
            try:
                start_time = time.perf_counter()
                
                async with session.post(
                    f"{base_url}/detect-spam-batch",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    elapsed = time.perf_counter() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        items_per_sec = len(result) / elapsed
                        status = "✅ OK"
                        
                        results.append({
                            'size': batch_size,
                            'time': elapsed,
                            'items_per_sec': items_per_sec,
                            'success': True
                        })
                        
                    else:
                        items_per_sec = 0
                        status = f"❌ {response.status}"
                        
                        results.append({
                            'size': batch_size,
                            'time': elapsed,
                            'items_per_sec': 0,
                            'success': False
                        })
                    
                    print(f"{batch_size:4d} | {elapsed:6.2f}s | {items_per_sec:8.1f} | {status}")
                    
            except Exception as e:
                print(f"{batch_size:4d} | {'ERROR':>6} | {'0.0':>8} | ❌ {str(e)[:20]}")
                results.append({
                    'size': batch_size,
                    'time': 0,
                    'items_per_sec': 0,
                    'success': False
                })
        
        # Analysis
        successful_results = [r for r in results if r['success']]
        
        if successful_results:
            print(f"\n📊 ANALYSIS:")
            print(f"=" * 40)
            
            # Find best throughput
            best_throughput = max(successful_results, key=lambda x: x['items_per_sec'])
            print(f"🏆 Best Throughput: {best_throughput['size']} items")
            print(f"   └─ {best_throughput['items_per_sec']:.1f} items/second")
            
            # Find fastest response
            fastest_response = min(successful_results, key=lambda x: x['time'])
            print(f"⚡ Fastest Response: {fastest_response['size']} items")
            print(f"   └─ {fastest_response['time']:.2f} seconds")
            
            # Efficiency analysis
            efficiency_scores = []
            for r in successful_results:
                # Score = throughput / (time penalty for large batches)
                time_penalty = 1 + (r['time'] - 1) * 0.1  # Slight penalty for longer times
                efficiency = r['items_per_sec'] / time_penalty
                efficiency_scores.append((r['size'], efficiency))
            
            best_efficiency = max(efficiency_scores, key=lambda x: x[1])
            print(f"🎯 Most Efficient: {best_efficiency[0]} items")
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            
            if best_throughput['size'] <= 20:
                print(f"   • Optimal batch size: {best_throughput['size']}-{best_throughput['size']+10}")
                print(f"   • Good for: Real-time processing")
            elif best_throughput['size'] <= 50:
                print(f"   • Optimal batch size: {best_throughput['size']}")
                print(f"   • Good for: Balanced performance")
            else:
                print(f"   • Optimal batch size: {best_throughput['size']}")
                print(f"   • Good for: High-volume processing")
                print(f"   • Warning: Monitor memory usage")
            
            # Calculate projected performance
            best_rps = best_throughput['items_per_sec']
            projected_per_minute = best_rps * 60
            
            print(f"\n📈 PROJECTED PERFORMANCE:")
            print(f"   • {best_rps:.1f} items/second")
            print(f"   • {projected_per_minute:.0f} items/minute")
            
            if projected_per_minute >= 8000:
                print(f"   • ✅ Meets 8k-10k/minute target!")
            else:
                print(f"   • ⚠️ Below 8k/minute target")
                print(f"   • Consider: More concurrent batches or larger batch size")
        
        else:
            print("❌ No successful batch tests")


if __name__ == "__main__":
    asyncio.run(test_batch_performance())