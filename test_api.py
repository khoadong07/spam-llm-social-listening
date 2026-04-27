#!/usr/bin/env python3
"""
Test script for spam detection API
"""
import asyncio
import httpx
import json

# Test data
test_data = {
    "id": "10238500853796158_1439407534649725",
    "index": "5cf117c8f2bff1e200c7d49b",
    "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà ? #congtytaichinh #fecredit #homecredit #vaytienonline",
    "content": "Mình bùng home có 7 triệu mà 6 tháng nó xuống nhà còn vay nhanh momo mình bùng 25 triệu hơn 1 năm rưỡi chưa thấy ai xuống hay gửi giấy về nhà là sao vậy bạn?",
    "description": "",
    "type": "tiktokComment",
    "category": "Finance"
}

async def test_single_request():
    """Test single spam detection request"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/detect-spam",
                json=test_data,
                timeout=30.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

async def test_batch_request():
    """Test batch spam detection request"""
    batch_data = [test_data, test_data.copy()]
    batch_data[1]["id"] = "different_id"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/detect-spam-batch",
                json=batch_data,
                timeout=60.0
            )
            print(f"Batch Status: {response.status_code}")
            print(f"Batch Response: {response.json()}")
        except Exception as e:
            print(f"Batch Error: {e}")

if __name__ == "__main__":
    print("Testing Spam Detection API...")
    asyncio.run(test_single_request())
    asyncio.run(test_batch_request())