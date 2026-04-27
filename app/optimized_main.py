from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List
import uvloop  # High-performance event loop
from app.models import SpamRequest, SpamResponse
from app.services.optimized_spam_detector import optimized_spam_detector
from app.config import settings

# Use uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

app = FastAPI(
    title="High-Performance Spam Detection Service",
    description="Optimized AI-powered spam detection for Vietnamese content",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "High-Performance Spam Detection Service is running", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "performance_mode": "optimized"}

@app.post("/detect-spam", response_model=SpamResponse)
async def detect_spam_single(request: SpamRequest):
    """Optimized single spam detection"""
    try:
        is_spam = await optimized_spam_detector.detect_spam_single(request)
        
        return SpamResponse(
            id=request.id,
            index=request.index,
            type=request.type,
            is_spam=is_spam
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/detect-spam-batch", response_model=List[SpamResponse])
async def detect_spam_batch(requests: List[SpamRequest]):
    """Optimized batch spam detection with size limit"""
    try:
        if len(requests) > settings.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch size {len(requests)} exceeds maximum {settings.MAX_BATCH_SIZE}"
            )
        
        # Use optimized batch processing
        spam_results = await optimized_spam_detector.detect_spam_batch(requests)
        
        responses = []
        for i, request in enumerate(requests):
            responses.append(SpamResponse(
                id=request.id,
                index=request.index,
                type=request.type,
                is_spam=spam_results[i]
            ))
        
        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

@app.post("/detect-spam-mega-batch", response_model=List[SpamResponse])
async def detect_spam_mega_batch(requests: List[SpamRequest]):
    """Ultra-optimized mega batch processing for maximum throughput"""
    try:
        if len(requests) > 1000:  # Hard limit
            raise HTTPException(status_code=400, detail="Mega batch size cannot exceed 1000")
        
        # Split into smaller chunks for optimal processing
        chunk_size = 50
        chunks = [requests[i:i + chunk_size] for i in range(0, len(requests), chunk_size)]
        
        # Process chunks concurrently
        chunk_tasks = [optimized_spam_detector.detect_spam_batch(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*chunk_tasks)
        
        # Flatten results
        all_results = []
        for chunk_result in chunk_results:
            all_results.extend(chunk_result)
        
        # Build responses
        responses = []
        for i, request in enumerate(requests):
            responses.append(SpamResponse(
                id=request.id,
                index=request.index,
                type=request.type,
                is_spam=all_results[i]
            ))
        
        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing mega batch: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get performance statistics"""
    return {
        "max_concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
        "max_batch_size": settings.MAX_BATCH_SIZE,
        "memory_cache_size": settings.MEMORY_CACHE_SIZE,
        "redis_pool_size": settings.REDIS_POOL_SIZE,
        "cache_ttl_hours": settings.CACHE_TTL // 3600,
        "performance_optimizations": [
            "uvloop event loop",
            "HTTP/2 support", 
            "Connection pooling",
            "In-memory + Redis caching",
            "LRU cache for prompts",
            "Batch processing",
            "Fire-and-forget cache writes"
        ]
    }

@app.on_event("startup")
async def startup_event():
    """Initialize optimized components"""
    print("🚀 Starting High-Performance Spam Detection Service...")
    print(f"📊 Max concurrent requests: {settings.MAX_CONCURRENT_REQUESTS}")
    print(f"📦 Max batch size: {settings.MAX_BATCH_SIZE}")
    print(f"💾 Memory cache size: {settings.MEMORY_CACHE_SIZE}")
    print(f"🔗 Redis pool size: {settings.REDIS_POOL_SIZE}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    await optimized_spam_detector.close()
    print("🛑 High-Performance Spam Detection Service stopped")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        loop="uvloop",  # Use uvloop
        workers=1,  # Single worker with high concurrency
        access_log=False,  # Disable access logs for performance
    )