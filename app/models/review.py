from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import BaseModel

class ReviewAggregate(BaseModel):
    __tablename__ = "reviews_aggregate"
    
    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    avg_rating = Column(Numeric(3, 2))  # 0.00 to 5.00
    total_reviews = Column(Integer, default=0)
    rating_breakdown = Column(JSONB, default={})
    source_url = Column(String(500))
    last_scraped_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tool = relationship("Tool", back_populates="reviews")
    
    def __repr__(self):
        return f"<ReviewAggregate(id={self.id}, tool_id={self.tool_id}, source='{self.source}')>"
