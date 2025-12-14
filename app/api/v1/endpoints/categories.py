# app/api/v1/endpoints/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_pagination import Page, paginate

from app.database.session import get_db
from app.schemas.category import Category, CategoryCreate, CategoryUpdate, CategoryInDB
from app.services.category_service import CategoryService

router = APIRouter()

@router.get("/", response_model=Page[Category])
def get_categories(
    db: Session = Depends(get_db),
    parent_id: Optional[int] = None,
    include_children: bool = False
):
    """
    Get list of categories, optionally filtered by parent_id.
    """
    categories = CategoryService.get_categories(db, parent_id=parent_id)
    return paginate(categories)

@router.get("/{category_id}", response_model=CategoryInDB)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
    category = CategoryService.get_category(db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.get("/{slug}/tools", response_model=List[dict])
def get_category_tools(
    slug: str,
    include_subcategories: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all tools in a category, optionally including subcategories.
    """
    return CategoryService.get_category_tools(
        db,
        slug=slug,
        include_subcategories=include_subcategories
    )

@router.post("/", response_model=CategoryInDB, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new category.
    """
    return CategoryService.create_category(db, category=category)

@router.put("/{category_id}", response_model=CategoryInDB)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a category.
    """
    updated_category = CategoryService.update_category(
        db,
        category_id=category_id,
        category=category
    )
    if not updated_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return updated_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a category.
    """
    success = CategoryService.delete_category(db, category_id=category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return None