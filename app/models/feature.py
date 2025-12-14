from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import BaseModel

class Feature(BaseModel):
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_name = Column(String(255), nullable=False)
    feature_category = Column(String(100))
    is_available = Column(Boolean, default=True)
    tier_availability = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tool = relationship("Tool", back_populates="features")
    
    def __repr__(self):
        return f"<Feature(id={self.id}, name='{self.feature_name}', tool_id={self.tool_id})>"
