from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import BaseModel

class Tool(BaseModel):
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    description = Column(Text)
    tagline = Column(String(500))
    website_url = Column(String(500))
    logo_url = Column(String(500))
    founded_date = Column(Date)
    company_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    query_count = Column(Integer, default=0)
    last_queried_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="tools")
    pricing_tiers = relationship("PricingTier", back_populates="tool", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="tool", cascade="all, delete-orphan")
    reviews = relationship("ReviewAggregate", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}')>"
