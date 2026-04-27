from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List
from app.models import SpamRequest, SpamResponse
from app.services.spam_detector import spam_detector

app = FastAPI(
    title="Spam Detection Service",
    description="AI-powered spam detection for Vietnamese content",
    version="1.0.0"
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
    return {"message": "Spam Detection Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/detect-spam", response_model=SpamResponse)
async def detect_spam_single(request: SpamRequest):
    """Detect spam for a single request"""
    try:
        is_spam = await spam_detector.detect_spam(request)
        
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
    """Detect spam for multiple requests concurrently"""
    try:
        # Process all requests concurrently
        tasks = [spam_detector.detect_spam(req) for req in requests]
        spam_results = await asyncio.gather(*tasks)
        
        responses = []
        for i, request in enumerate(requests):
            responses.append(SpamResponse(
                id=request.id,
                index=request.index,
                type=request.type,
                is_spam=spam_results[i]
            ))
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)