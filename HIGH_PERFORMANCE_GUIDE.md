# 🚀 High-Performance Spam Detection Guide

Hướng dẫn đạt 8-10k requests/phút (133-167 RPS)

## 🎯 Mục tiêu hiệu suất
- **Target**: 8,000-10,000 requests/minute
- **Peak RPS**: 133-167 requests/second
- **Response time**: P95 < 100ms
- **Cache hit rate**: 60%+

## 🔧 Các tối ưu hóa đã thực hiện

### 1. **Application Level**
- ✅ uvloop event loop (30% faster than asyncio)
- ✅ HTTP/2 support
- ✅ Connection pooling (1000 connections)
- ✅ In-memory + Redis dual caching
- ✅ LRU cache for prompt generation
- ✅ Fire-and-forget cache writes
- ✅ Optimized batch processing
- ✅ newsTopic instant bypass

### 2. **Redis Optimizations**
- ✅ Connection pooling (100 connections)
- ✅ Hiredis parser for speed
- ✅ LRU eviction policy
- ✅ TCP keepalive
- ✅ Optimized memory usage

### 3. **HTTP Client Optimizations**
- ✅ Increased concurrent requests (500)
- ✅ Reduced timeout (15s → 10s)
- ✅ HTTP/2 support
- ✅ Connection reuse
- ✅ Reduced retry attempts

### 4. **Memory Optimizations**
- ✅ In-memory cache (20k entries)
- ✅ LRU cache for hot data
- ✅ Reduced prompt size (100 → 80 words)
- ✅ Optimized JSON serialization

## 🚀 Deployment

### Quick Start (Optimized Version)
```bash
# Build and run optimized version
docker-compose -f docker-compose.optimized.yml up -d

# Check performance stats
curl http://localhost:8010/stats
```

### Manual Setup
```bash
# Install performance dependencies
pip install uvloop hiredis

# Run optimized version
python app/optimized_main.py
```

## 📊 Benchmark Tests

### 1. High-Performance Benchmark
```bash
python high_performance_benchmark.py
```

**Features:**
- 100 concurrent workers
- 60% newsTopic (instant bypass)
- 30% cache hits
- 10% new LLM calls
- Target: 8-10k requests/minute

### 2. Quick Performance Check
```bash
python quick_benchmark.py
```

## 🎛️ Performance Tuning

### Environment Variables
```bash
# Core performance
MAX_CONCURRENT_REQUESTS=500    # Increase for more throughput
MAX_BATCH_SIZE=100            # Larger batches = better throughput
MEMORY_CACHE_SIZE=20000       # More memory cache = faster responses

# Redis tuning
REDIS_POOL_SIZE=100           # More connections = less blocking
REDIS_HOST=redis              # Use Redis hostname in Docker

# Enable optimizations
ENABLE_BATCH_PROCESSING=true
```

### Docker Resource Limits
```yaml
# Recommended resources
resources:
  limits:
    memory: 2G      # More memory for caching
    cpus: '2.0'     # More CPU for concurrency
  reservations:
    memory: 1G
    cpus: '1.0'
```

## 📈 Expected Performance

### With Optimizations:
- **newsTopic bypass**: 1-3ms (instant)
- **Memory cache hits**: 3-10ms
- **Redis cache hits**: 10-30ms  
- **Cold LLM calls**: 200-800ms
- **Overall RPS**: 150-200+ requests/second
- **Requests/minute**: 9,000-12,000+

### Performance Breakdown:
```
60% newsTopic (instant)     → 1-3ms
25% memory cache hits       → 3-10ms  
10% Redis cache hits        → 10-30ms
5% new LLM calls           → 200-800ms
```

## 🔍 Monitoring & Troubleshooting

### Check API Stats
```bash
curl http://localhost:8010/stats
```

### Monitor Docker Resources
```bash
docker stats
```

### Redis Performance
```bash
# Connect to Redis
docker exec -it redis redis-cli

# Check stats
INFO stats
INFO memory
```

### Common Issues & Solutions

#### 1. **Low RPS (< 100)**
```bash
# Check concurrent requests
curl http://localhost:8010/stats

# Increase concurrency
export MAX_CONCURRENT_REQUESTS=800
```

#### 2. **High Response Times**
```bash
# Check cache hit rate
# Should be 60%+ for optimal performance

# Increase memory cache
export MEMORY_CACHE_SIZE=50000
```

#### 3. **Redis Connection Errors**
```bash
# Check Redis logs
docker logs redis

# Increase Redis pool
export REDIS_POOL_SIZE=200
```

#### 4. **Memory Issues**
```bash
# Increase Docker memory limit
# Edit docker-compose.optimized.yml
memory: 4G
```

## 🚀 Scaling Beyond 10k/minute

### Horizontal Scaling
```yaml
# Load balancer + multiple instances
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "8010:80"
    # Load balance across multiple API instances
  
  spam-api-1:
    # Instance 1
  spam-api-2:
    # Instance 2
  spam-api-3:
    # Instance 3
```

### Advanced Optimizations
1. **CDN caching** for static responses
2. **Database connection pooling** if using DB
3. **Async queue processing** for non-critical requests
4. **GPU acceleration** for LLM inference
5. **Edge computing** deployment

## 📊 Benchmark Results Target

```
🏆 HIGH THROUGHPUT SINGLE REQUESTS
====================================
⏱️  Duration: 60.00s
📨 Total Requests: 12,450
✅ Successful: 12,380
❌ Failed: 70
📈 Success Rate: 99.44%
🚀 Requests/Second: 206.33
🎯 Requests/Minute: 12,380
⚡ Avg Response: 25.30ms
🏃 Min Response: 1.20ms
🐌 Max Response: 850.40ms
📊 P95 Response: 45.20ms
📊 P99 Response: 120.80ms
💾 Cache Hit Est: 85.2%
🎯 8-10k/min Target: 🎉 TARGET ACHIEVED!
```

## 🎉 Success Criteria

✅ **8,000+ requests/minute**: Minimum target  
✅ **10,000+ requests/minute**: Excellent performance  
✅ **P95 < 100ms**: Good user experience  
✅ **99%+ success rate**: Reliable service  
✅ **60%+ cache hit rate**: Efficient caching  

Với các tối ưu hóa này, hệ thống có thể đạt 10k+ requests/minute một cách ổn định!