# app/database/models/integration.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from app.database.base import BaseModel
from sqlalchemy.orm import relationship

class Integration(BaseModel):
    __tablename__ = "integrations"
    
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    integrates_with = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_type = Column(String(20))  # native, api, webhook, zapier
    ease_of_setup = Column(String(10))  # easy, medium, complex
    documentation_url = Column(String(500))
    is_official = Column(Boolean, default=False)
    
    # Relationships
    tool = relationship("Tool", foreign_keys=[tool_id], backref="integrations_out")
    integrated_tool = relationship("Tool", foreign_keys=[integrates_with])
    
    def __repr__(self):
        return f"<Integration(tool_id={self.tool_id}, integrates_with={self.integrates_with}, type='{self.integration_type}')>"