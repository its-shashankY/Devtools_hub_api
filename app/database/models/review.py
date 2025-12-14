# app/database/models/review.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.database.base import BaseModel
from sqlalchemy.orm import relationship

class ReviewAggregate(BaseModel):
    __tablename__ = "reviews_aggregate"
    
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    avg_rating = Column(Numeric(3, 2))
    total_reviews = Column(Integer, default=0)
    rating_breakdown = Column(JSONB, default={})
    source_url = Column(String(500))
    last_scraped_at = Column(DateTime(timezone=True))
    
    # Relationships
    tool = relationship("Tool", back_populates="reviews")
    
    def __repr__(self):
        return f"<ReviewAggregate(id={self.id}, tool_id={self.tool_id}, source='{self.source}')>"