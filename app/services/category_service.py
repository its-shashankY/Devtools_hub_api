# app/services/category_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.category import Category
from app.models.tool import Tool
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryService:
    @staticmethod
    def get_categories(
        db: Session,
        parent_id: Optional[int] = None,
        include_children: bool = False
    ):
        query = db.query(Category)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        elif not include_children:
            query = query.filter(Category.parent_id.is_(None))
            
        return query.order_by(Category.display_order, Category.name).all()

    @staticmethod
    def get_category(db: Session, category_id: int):
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_category_by_slug(db: Session, slug: str):
        return db.query(Category).filter(Category.slug == slug).first()

    @staticmethod
    def get_category_tools(
        db: Session,
        slug: str,
        include_subcategories: bool = True
    ):
        category = CategoryService.get_category_by_slug(db, slug=slug)
        if not category:
            return []
            
        category_ids = [category.id]
        
        if include_subcategories:
            # Get all descendant category IDs
            def get_child_ids(cat_id):
                children = db.query(Category).filter(Category.parent_id == cat_id).all()
                ids = [c.id for c in children]
                for child in children:
                    ids.extend(get_child_ids(child.id))
                return ids
                
            category_ids.extend(get_child_ids(category.id))
        
        # Get tools in these categories
        tools = db.query(Tool).filter(Tool.category_id.in_(category_ids)).all()
        return tools

    @staticmethod
    def create_category(db: Session, category: CategoryCreate):
        db_category = Category(**category.dict())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

    @staticmethod
    def update_category(
        db: Session,
        category_id: int,
        category: CategoryUpdate
    ):
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return None
            
        update_data = category.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
            
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category

    @staticmethod
    def delete_category(db: Session, category_id: int):
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return False
            
        db.delete(category)
        db.commit()
        return True