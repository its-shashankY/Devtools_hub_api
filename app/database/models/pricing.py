# app/database/models/pricing.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from app.database.base import BaseModel
from sqlalchemy.orm import relationship

class PricingTier(BaseModel):
    __tablename__ = "pricing_tiers"
    
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    tier_name = Column(String(100), nullable=False)
    monthly_price = Column(Numeric(10, 2))
    annual_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String(20))  # monthly, annual, one-time
    features_json = Column(JSONB, default={})
    limits_json = Column(JSONB, default={})
    is_current = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True))
    effective_to = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tool = relationship("Tool", back_populates="pricing_tiers")
    
    def __repr__(self):
        return f"<PricingTier(id={self.id}, tier='{self.tier_name}', tool_id={self.tool_id})>"