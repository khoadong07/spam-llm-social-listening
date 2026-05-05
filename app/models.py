from pydantic import BaseModel
from typing import Optional, Literal

class SpamRequest(BaseModel):
    id: str
    index: str
    title: Optional[str] = ""
    content: str
    description: Optional[str] = ""
    site_id: Optional[str] = ""  # Added for excluded sites filter
    type: Literal[
        "fbPageComment", "fbGroupComment", "fbUserComment", "forumComment",
        "newsComment", "youtubeComment", "tiktokComment", "snsComment",
        "linkedinComment", "ecommerceComment", "threadsComment",
        "fbPageTopic", "fbGroupTopic", "fbUserTopic", "forumTopic",
        "newsTopic", "youtubeTopic", "tiktokTopic", "snsTopic",
        "linkedinTopic", "ecommerceTopic", "threadsTopic"
    ]
    category: Literal[
        "Consumer Discretionary", "Communication Services", "Consumer Staples",
        "Information Tech", "Healthcare", "Industrials", "Energy",
        "Education", "Real Estate", "Finance", "Digital Payment"
    ]

class SpamResponse(BaseModel):
    id: str
    index: str
    type: str
    is_spam: bool