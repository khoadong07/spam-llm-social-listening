# 🚀 Spam Detection API Benchmark

Các script benchmark để test hiệu suất của Spam Detection API.

## 📋 Yêu cầu

```bash
pip install aiohttp
```

## 🧪 Các loại test

### 1. Quick Benchmark (`quick_benchmark.py`)
Test nhanh với 100 requests đồng thời để kiểm tra cơ bản:

```bash
python quick_benchmark.py
```

**Tính năng:**
- Health check API
- Test newsTopic bypass
- 100 concurrent requests
- Test cache performance
- Ước tính RPS tối đa

### 2. Full Benchmark (`benchmark_test.py`)
Test chi tiết trong 60 giây với nhiều kịch bản:

```bash
python benchmark_test.py
```

**Tính năng:**
- Single request benchmark (60s)
- Batch request benchmark với batch size 5 và 10
- Đo cache hit rate
- Thống kê chi tiết (P95, min/max response time)
- So sánh hiệu suất các phương pháp

## 📊 Kết quả mong đợi

### Với Cache Redis:
- **Cold requests**: 200-500ms (gọi LLM)
- **Cache hits**: 5-20ms
- **newsTopic bypass**: 1-5ms
- **Estimated RPS**: 50-200 requests/second

### Các yếu tố ảnh hưởng:
- Tốc độ mạng tới DeepInfra API
- Hiệu suất Redis
- Concurrent request limit (120)
- Cache hit rate

## 🔧 Cấu hình test

### Quick Benchmark:
- 100 concurrent requests
- Test data đa dạng
- Cache performance test

### Full Benchmark:
- 60 giây mỗi test
- 20 workers cho single requests
- 5 workers cho batch requests
- Semaphore limit: 50 (single), 10 (batch)

## 📈 Cách đọc kết quả

```
📊 SINGLE REQUEST BENCHMARK RESULTS
====================================
⏱️  Duration: 60.00 seconds
📨 Total Requests: 3,245
✅ Successful: 3,200
❌ Failed: 45
📈 Success Rate: 98.61%
🚀 Requests/Second: 53.33
⚡ Avg Response Time: 187.50ms
🏃 Min Response Time: 8.20ms
🐌 Max Response Time: 2,450.30ms
📊 P95 Response Time: 450.20ms
💾 Cache Hit Rate: 25.30%
```

### Giải thích:
- **Requests/Second**: Số request thành công mỗi giây
- **Cache Hit Rate**: % request được phục vụ từ cache
- **P95 Response Time**: 95% requests có thời gian phản hồi dưới giá trị này
- **Success Rate**: Tỷ lệ request thành công

## 🎯 Mục tiêu hiệu suất

- **Target RPS**: 100+ requests/second
- **Cache Hit Rate**: 30%+ (với dữ liệu lặp lại)
- **P95 Response Time**: <500ms
- **Success Rate**: >95%

## 🚨 Lưu ý

1. **Khởi động API trước khi test:**
   ```bash
   docker-compose up -d
   ```

2. **Kiểm tra Redis hoạt động:**
   ```bash
   docker-compose logs redis
   ```

3. **Monitor resource usage:**
   ```bash
   docker stats
   ```

4. **Test với dữ liệu thực tế** để có kết quả chính xác hơn

## 🔍 Troubleshooting

### API không phản hồi:
```bash
curl http://localhost:8010/health
```

### Redis connection issues:
```bash
docker-compose logs spam-detection-api | grep -i redis
```

### High response times:
- Kiểm tra DeepInfra API status
- Monitor Docker container resources
- Kiểm tra network latency