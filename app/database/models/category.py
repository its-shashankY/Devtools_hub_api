# app/database/models/category.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base  # ✅ Change this

class Category(Base):  # ✅ Change this
    __tablename__ = "categories"
    __table_args__ = {'extend_existing': True}  # Add this temporarily
    
    id = Column(Integer, primary_key=True, index=True)  # ✅ Add explicit id column
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    description = Column(Text)
    icon = Column(String(100))
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id", backref="children")
    tools = relationship("Tool", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"