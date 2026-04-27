#!/usr/bin/env python3
"""
Benchmark test cho Spam Detection API
Test tốc độ xử lý trong 1 phút với các kịch bản khác nhau
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class BenchmarkResult:
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    cache_hit_rate: float
    duration_seconds: float


class SpamDetectionBenchmark:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=200)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Tạo dữ liệu test với các loại content khác nhau"""
        test_cases = [
            # Normal content
            {
                "id": f"test_{i}",
                "index": f"idx_{i}",
                "title": "Hỏi về sản phẩm công nghệ",
                "content": "Mọi người cho em hỏi về laptop gaming tầm 20 triệu có gì tốt không ạ?",
                "description": "Tư vấn mua laptop",
                "type": "forumTopic",
                "category": "Information Tech"
            },
            # Spam content
            {
                "id": f"test_{i}",
                "index": f"idx_{i}",
                "title": "BÁN HÀNG GIÁ RẺ",
                "content": "Liên hệ Zalo 0123456789 để mua hàng giá rẻ nhất thị trường!!!",
                "description": "Quảng cáo bán hàng",
                "type": "fbGroupTopic",
                "category": "Consumer Discretionary"
            },
            # newsTopic (should bypass)
            {
                "id": f"test_{i}",
                "index": f"idx_{i}",
                "title": "Tin tức công nghệ mới",
                "content": "Apple vừa ra mắt iPhone mới với nhiều tính năng đột phá",
                "description": "Tin tức công nghệ",
                "type": "newsTopic",
                "category": "Information Tech"
            },
            # Real estate content
            {
                "id": f"test_{i}",
                "index": f"idx_{i}",
                "title": "Tìm hiểu về thị trường BĐS",
                "content": "Thị trường bất động sản hiện tại có xu hướng như thế nào?",
                "description": "Thảo luận BĐS",
                "type": "forumTopic",
                "category": "Real Estate"
            }
        ]
        
        # Tạo dữ liệu với pattern lặp lại để test cache
        result = []
        for i in range(count):
            template = test_cases[i % len(test_cases)].copy()
            template["id"] = f"test_{i}"
            template["index"] = f"idx_{i}"
            result.append(template)
        
        return result

    async def single_request(self, data: Dict[str, Any]) -> tuple[bool, float, bool]:
        """Gửi một request và đo thời gian phản hồi"""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}/detect-spam",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    # Kiểm tra cache hit (response time < 50ms có thể là cache hit)
                    is_cache_hit = response_time < 0.05
                    return True, response_time, is_cache_hit
                else:
                    return False, response_time, False
                    
        except Exception as e:
            response_time = time.time() - start_time
            print(f"Request failed: {e}")
            return False, response_time, False

    async def batch_request(self, data_list: List[Dict[str, Any]]) -> tuple[bool, float, int]:
        """Gửi batch request"""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}/detect-spam-batch",
                json=data_list,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    return True, response_time, len(result)
                else:
                    return False, response_time, 0
                    
        except Exception as e:
            response_time = time.time() - start_time
            print(f"Batch request failed: {e}")
            return False, response_time, 0

    async def run_single_request_benchmark(self, duration_seconds: int = 60) -> BenchmarkResult:
        """Benchmark với single requests"""
        print(f"🚀 Starting single request benchmark for {duration_seconds} seconds...")
        
        test_data = self.generate_test_data(1000)  # Tạo pool dữ liệu test
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        cache_hits = 0
        
        # Tạo semaphore để giới hạn concurrent requests
        semaphore = asyncio.Semaphore(50)
        
        async def worker():
            nonlocal total_requests, successful_requests, failed_requests, cache_hits
            
            while time.time() < end_time:
                async with semaphore:
                    data = test_data[total_requests % len(test_data)]
                    success, response_time, is_cache_hit = await self.single_request(data)
                    
                    total_requests += 1
                    response_times.append(response_time)
                    
                    if success:
                        successful_requests += 1
                        if is_cache_hit:
                            cache_hits += 1
                    else:
                        failed_requests += 1
        
        # Chạy nhiều workers đồng thời
        workers = [asyncio.create_task(worker()) for _ in range(20)]
        await asyncio.gather(*workers, return_exceptions=True)
        
        actual_duration = time.time() - start_time
        
        return BenchmarkResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=successful_requests / actual_duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            cache_hit_rate=(cache_hits / successful_requests * 100) if successful_requests > 0 else 0,
            duration_seconds=actual_duration
        )

    async def run_batch_request_benchmark(self, duration_seconds: int = 60, batch_size: int = 10) -> BenchmarkResult:
        """Benchmark với batch requests"""
        print(f"🚀 Starting batch request benchmark (batch size: {batch_size}) for {duration_seconds} seconds...")
        
        test_data = self.generate_test_data(1000)
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        semaphore = asyncio.Semaphore(10)  # Ít concurrent batches hơn
        
        async def worker():
            nonlocal total_requests, successful_requests, failed_requests
            
            batch_index = 0
            while time.time() < end_time:
                async with semaphore:
                    # Tạo batch
                    batch_data = []
                    for i in range(batch_size):
                        data = test_data[(batch_index * batch_size + i) % len(test_data)]
                        batch_data.append(data)
                    
                    success, response_time, processed_count = await self.batch_request(batch_data)
                    
                    total_requests += len(batch_data)
                    response_times.append(response_time)
                    
                    if success:
                        successful_requests += processed_count
                        failed_requests += len(batch_data) - processed_count
                    else:
                        failed_requests += len(batch_data)
                    
                    batch_index += 1
        
        workers = [asyncio.create_task(worker()) for _ in range(5)]
        await asyncio.gather(*workers, return_exceptions=True)
        
        actual_duration = time.time() - start_time
        
        return BenchmarkResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=successful_requests / actual_duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
            cache_hit_rate=0,  # Không tính cache hit rate cho batch
            duration_seconds=actual_duration
        )

    async def health_check(self) -> bool:
        """Kiểm tra API có hoạt động không"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False

    def print_results(self, result: BenchmarkResult, test_name: str):
        """In kết quả benchmark"""
        print(f"\n{'='*60}")
        print(f"📊 {test_name} RESULTS")
        print(f"{'='*60}")
        print(f"⏱️  Duration: {result.duration_seconds:.2f} seconds")
        print(f"📨 Total Requests: {result.total_requests:,}")
        print(f"✅ Successful: {result.successful_requests:,}")
        print(f"❌ Failed: {result.failed_requests:,}")
        print(f"📈 Success Rate: {(result.successful_requests/result.total_requests*100):.2f}%")
        print(f"🚀 Requests/Second: {result.requests_per_second:.2f}")
        print(f"⚡ Avg Response Time: {result.avg_response_time*1000:.2f}ms")
        print(f"🏃 Min Response Time: {result.min_response_time*1000:.2f}ms")
        print(f"🐌 Max Response Time: {result.max_response_time*1000:.2f}ms")
        print(f"📊 P95 Response Time: {result.p95_response_time*1000:.2f}ms")
        if result.cache_hit_rate > 0:
            print(f"💾 Cache Hit Rate: {result.cache_hit_rate:.2f}%")
        print(f"{'='*60}")


async def main():
    """Chạy tất cả benchmark tests"""
    print("🔥 SPAM DETECTION API BENCHMARK TEST")
    print("=" * 60)
    
    async with SpamDetectionBenchmark() as benchmark:
        # Health check
        print("🏥 Checking API health...")
        if not await benchmark.health_check():
            print("❌ API is not responding. Please start the service first.")
            return
        print("✅ API is healthy!")
        
        # Warm up
        print("\n🔥 Warming up...")
        warm_up_data = benchmark.generate_test_data(10)
        for data in warm_up_data[:5]:
            await benchmark.single_request(data)
        print("✅ Warm up completed!")
        
        # Test 1: Single requests
        result1 = await benchmark.run_single_request_benchmark(60)
        benchmark.print_results(result1, "SINGLE REQUEST BENCHMARK")
        
        # Test 2: Batch requests (size 5)
        result2 = await benchmark.run_batch_request_benchmark(60, batch_size=5)
        benchmark.print_results(result2, "BATCH REQUEST BENCHMARK (Size: 5)")
        
        # Test 3: Batch requests (size 10)
        result3 = await benchmark.run_batch_request_benchmark(60, batch_size=10)
        benchmark.print_results(result3, "BATCH REQUEST BENCHMARK (Size: 10)")
        
        # Summary
        print(f"\n🏆 SUMMARY - MAXIMUM THROUGHPUT")
        print(f"{'='*60}")
        max_rps = max(result1.requests_per_second, result2.requests_per_second, result3.requests_per_second)
        best_test = "Single Request" if result1.requests_per_second == max_rps else \
                   "Batch Size 5" if result2.requests_per_second == max_rps else "Batch Size 10"
        
        print(f"🥇 Best Performance: {best_test}")
        print(f"🚀 Maximum RPS: {max_rps:.2f} requests/second")
        print(f"📊 Requests per minute: {max_rps * 60:.0f}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())