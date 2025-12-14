# app/database/models/tool.py
from sqlalchemy import Column, String, Text, Date, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import BaseModel

class Tool(BaseModel):
    __tablename__ = "tools"
    
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
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
    
    # Relationships
    category = relationship("Category", back_populates="tools")
    pricing_tiers = relationship("PricingTier", back_populates="tool", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="tool", cascade="all, delete-orphan")
    reviews = relationship("ReviewAggregate", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}')>"