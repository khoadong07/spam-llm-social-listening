#!/usr/bin/env python3
"""
Batch Size Optimizer - Tìm batch size tối ưu cho spam detection
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class BatchTestResult:
    batch_size: int
    total_items: int
    total_time: float
    items_per_second: float
    avg_response_time: float
    success_rate: float
    memory_usage_estimate: str
    recommendation: str


class BatchSizeOptimizer:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=500, limit_per_host=300)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate diverse test data for batch testing"""
        base_cases = [
            # newsTopic (instant bypass) - 40%
            {
                "title": "Tin tức công nghệ",
                "content": "Apple ra mắt iPhone mới với nhiều tính năng đột phá",
                "description": "Tin tức",
                "type": "newsTopic",
                "category": "Information Tech"
            },
            # Cache hit cases - 30%
            {
                "title": "Hỏi về laptop gaming",
                "content": "Mọi người tư vấn laptop gaming tầm 20 triệu",
                "description": "Tư vấn",
                "type": "forumTopic",
                "category": "Information Tech"
            },
            # Finance discussion - 20%
            {
                "title": "Thảo luận về đầu tư",
                "content": "Mọi người nghĩ sao về việc đầu tư chứng khoán hiện tại?",
                "description": "Thảo luận tài chính",
                "type": "forumTopic",
                "category": "Finance"
            },
            # Spam case - 10%
            {
                "title": "BÁN HÀNG GIÁ RẺ",
                "content": "Liên hệ Zalo 0123456789 để mua hàng giá rẻ",
                "description": "Quảng cáo",
                "type": "fbGroupTopic",
                "category": "Consumer Discretionary"
            }
        ]
        
        result = []
        for i in range(count):
            # Distribution: 40% newsTopic, 30% cache hits, 20% finance, 10% spam
            if i % 10 < 4:
                template = base_cases[0].copy()  # newsTopic
            elif i % 10 < 7:
                template = base_cases[1].copy()  # cache hit
            elif i % 10 < 9:
                template = base_cases[2].copy()  # finance
            else:
                template = base_cases[3].copy()  # spam
                template["content"] = f"Unique spam {i} - " + template["content"]
            
            template["id"] = f"batch_test_{i}"
            template["index"] = f"idx_{i}"
            result.append(template)
        
        return result

    async def test_batch_size(self, batch_size: int, total_items: int = 200) -> BatchTestResult:
        """Test specific batch size performance"""
        print(f"🧪 Testing batch size: {batch_size} (Total items: {total_items})")
        
        test_data = self.generate_test_data(total_items)
        
        # Split into batches
        batches = [test_data[i:i + batch_size] for i in range(0, len(test_data), batch_size)]
        
        start_time = time.perf_counter()
        successful_items = 0
        failed_items = 0
        response_times = []
        
        # Process batches sequentially to measure pure batch performance
        for batch in batches:
            batch_start = time.perf_counter()
            
            try:
                async with self.session.post(
                    f"{self.base_url}/detect-spam-batch",
                    json=batch,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    batch_time = time.perf_counter() - batch_start
                    response_times.append(batch_time)
                    
                    if response.status == 200:
                        result = await response.json()
                        successful_items += len(result)
                    else:
                        failed_items += len(batch)
                        print(f"   ❌ Batch failed with status: {response.status}")
                        
            except Exception as e:
                batch_time = time.perf_counter() - batch_start
                response_times.append(batch_time)
                failed_items += len(batch)
                print(f"   ❌ Batch exception: {e}")
        
        total_time = time.perf_counter() - start_time
        
        # Calculate metrics
        items_per_second = successful_items / total_time if total_time > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        success_rate = (successful_items / total_items * 100) if total_items > 0 else 0
        
        # Memory usage estimate
        memory_per_item = 2  # KB per item estimate
        memory_usage = batch_size * memory_per_item
        if memory_usage < 100:
            memory_estimate = f"{memory_usage}KB (Low)"
        elif memory_usage < 500:
            memory_estimate = f"{memory_usage}KB (Medium)"
        else:
            memory_estimate = f"{memory_usage}KB (High)"
        
        # Recommendation
        if success_rate < 95:
            recommendation = "❌ Too high - causes failures"
        elif avg_response_time > 10:
            recommendation = "⚠️ Too high - slow response"
        elif items_per_second < 50:
            recommendation = "⚠️ Too low - poor throughput"
        elif batch_size < 10:
            recommendation = "⚠️ Too small - overhead"
        else:
            recommendation = "✅ Good performance"
        
        return BatchTestResult(
            batch_size=batch_size,
            total_items=total_items,
            total_time=total_time,
            items_per_second=items_per_second,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            memory_usage_estimate=memory_estimate,
            recommendation=recommendation
        )

    async def find_optimal_batch_size(self) -> BatchTestResult:
        """Find optimal batch size by testing multiple sizes"""
        
        print("🔍 FINDING OPTIMAL BATCH SIZE")
        print("=" * 60)
        
        # Health check
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    raise Exception("API not healthy")
            print("✅ API is healthy")
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return None
        
        # Test different batch sizes
        batch_sizes = [1, 5, 10, 20, 30, 50, 75, 100, 150, 200]
        results = []
        
        for batch_size in batch_sizes:
            try:
                result = await self.test_batch_size(batch_size, total_items=200)
                results.append(result)
                
                print(f"   📊 {batch_size:3d} items: {result.items_per_second:6.1f} items/s, "
                      f"{result.avg_response_time:5.2f}s avg, {result.success_rate:5.1f}% success")
                
                # Stop if performance degrades significantly
                if result.success_rate < 90:
                    print(f"   ⚠️ Stopping at batch size {batch_size} due to low success rate")
                    break
                    
            except Exception as e:
                print(f"   ❌ Failed to test batch size {batch_size}: {e}")
        
        if not results:
            print("❌ No successful tests")
            return None
        
        # Find optimal batch size
        # Prioritize: success_rate > 95%, then highest items_per_second
        valid_results = [r for r in results if r.success_rate >= 95]
        
        if not valid_results:
            print("⚠️ No batch sizes achieved 95% success rate")
            valid_results = results
        
        # Find best throughput among valid results
        optimal = max(valid_results, key=lambda r: r.items_per_second)
        
        return optimal, results

    def print_detailed_results(self, optimal: BatchTestResult, all_results: List[BatchTestResult]):
        """Print detailed analysis"""
        
        print(f"\n{'='*80}")
        print(f"📊 BATCH SIZE OPTIMIZATION RESULTS")
        print(f"{'='*80}")
        
        # Table header
        print(f"{'Size':>4} | {'Items/s':>8} | {'Avg Time':>8} | {'Success':>7} | {'Memory':>10} | {'Status'}")
        print(f"{'-'*4}-+-{'-'*8}-+-{'-'*8}-+-{'-'*7}-+-{'-'*10}-+-{'-'*20}")
        
        # Table rows
        for result in all_results:
            status_icon = "🏆" if result == optimal else "✅" if "Good" in result.recommendation else "⚠️" if "Too" in result.recommendation else "❌"
            
            print(f"{result.batch_size:4d} | {result.items_per_second:8.1f} | "
                  f"{result.avg_response_time:8.2f}s | {result.success_rate:6.1f}% | "
                  f"{result.memory_usage_estimate:>10} | {status_icon} {result.recommendation}")
        
        print(f"\n🏆 OPTIMAL BATCH SIZE: {optimal.batch_size}")
        print(f"{'='*80}")
        print(f"📈 Performance Metrics:")
        print(f"   • Throughput: {optimal.items_per_second:.1f} items/second")
        print(f"   • Response Time: {optimal.avg_response_time:.2f} seconds")
        print(f"   • Success Rate: {optimal.success_rate:.1f}%")
        print(f"   • Memory Usage: {optimal.memory_usage_estimate}")
        print(f"   • Total Time: {optimal.total_time:.2f}s for {optimal.total_items} items")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   • Set MAX_BATCH_SIZE = {optimal.batch_size}")
        print(f"   • Expected throughput: {optimal.items_per_second * 60:.0f} items/minute")
        
        # Additional recommendations based on results
        if optimal.batch_size < 20:
            print(f"   • Consider increasing concurrent requests for better throughput")
        elif optimal.batch_size > 100:
            print(f"   • Monitor memory usage and API rate limits")
        
        if optimal.avg_response_time > 5:
            print(f"   • Response time is high, consider optimizing cache hit rate")
        
        print(f"{'='*80}")


async def main():
    """Main optimization function"""
    
    async with BatchSizeOptimizer() as optimizer:
        optimal, all_results = await optimizer.find_optimal_batch_size()
        
        if optimal:
            optimizer.print_detailed_results(optimal, all_results)
            
            # Generate config recommendation
            print(f"\n🔧 CONFIGURATION UPDATE:")
            print(f"Add to your .env file:")
            print(f"MAX_BATCH_SIZE={optimal.batch_size}")
            
        else:
            print("❌ Could not determine optimal batch size")


if __name__ == "__main__":
    asyncio.run(main())