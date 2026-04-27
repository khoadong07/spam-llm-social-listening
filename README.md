# Spam Detection Service

FastAPI service sử dụng Meta-Llama-3.1-8B-Instruct-Turbo để phát hiện spam trong nội dung tiếng Việt.

## Tính năng

- Xử lý đồng thời tối đa 120 requests
- Hỗ trợ nhiều loại content: Comment và Topic
- Quy tắc đặc biệt cho Real Estate
- API đơn lẻ và batch processing
- Docker support

## Cài đặt

### 1. Clone và setup

```bash
git clone <repo-url>
cd spam-detection-service
cp .env.example .env
# Điền DEEPINFRA_TOKEN vào file .env
```

### 2. Chạy với Docker

```bash
docker-compose up --build
```

### 3. Chạy local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### Single Request
```bash
curl -X POST "http://localhost:8000/detect-spam" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "index": "idx_123",
    "title": "Nợ cty tài chính bao nhiêu thì bị xuống nhà?",
    "content": "Mình bùng home có 7 triệu...",
    "description": "",
    "type": "tiktokComment",
    "category": "Finance"
  }'
```

### Batch Request
```bash
curl -X POST "http://localhost:8000/detect-spam-batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "123",
      "index": "idx_123",
      "title": "Bán hàng online",
      "content": "Bán áo thun giá rẻ chỉ 99k, inbox mua ngay!",
      "type": "fbPageComment",
      "category": "Consumer Discretionary"
    }
  ]'
```

## Spam Detection Rules

### SPAM Criteria:
1. **Tin rao vặt thương mại** (trừ Real Estate)
2. **Link spam và nội dung 18+**
3. **Tiếng Việt lỗi font**: "t0i", "đươc", "4u", "2day"
4. **Viết tắt toàn bộ**: "e cần mua đt mới, ai bt chỗ nào bán rẻ k?"
5. **Nội dung không liên quan**

### NOT SPAM:
- Câu hỏi thật về tài chính, bất động sản
- Tin rao vặt Real Estate
- Thảo luận có ý nghĩa
- Tiếng Việt đúng chính tả

## Testing

```bash
# Test various spam scenarios
python test_spam_cases.py

# Test basic API
python test_api.py
```

## Response Format

```json
{
  "id": "123",
  "index": "idx_123", 
  "type": "tiktokComment",
  "is_spam": false
}
```