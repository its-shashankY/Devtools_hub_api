# app/services/tool_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status

from app.models.tool import Tool
from app.models.category import Category
from app.models.pricing import PricingTier
from app.models.feature import Feature
from app.models.review import ReviewAggregate
from app.schemas.tool import ToolCreate, ToolUpdate

class ToolService:
    @staticmethod
    def get_tools(
        db: Session,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        features: Optional[List[str]] = None,
        sort: str = "name",
        skip: int = 0,
        limit: int = 100
    ):
        query = db.query(Tool)
        
        # Apply filters
        if category:
            query = query.join(Category).filter(Category.name == category)
            
        if price_min is not None or price_max is not None:
            query = query.join(PricingTier)
            if price_min is not None:
                query = query.filter(PricingTier.monthly_price >= price_min)
            if price_max is not None:
                query = query.filter(PricingTier.monthly_price <= price_max)
            query = query.filter(PricingTier.is_current == True)
            
        if features:
            for feature in features:
                query = query.join(Feature).filter(
                    Feature.feature_name == feature,
                    Feature.is_available == True
                )
        
        # Apply sorting
        if sort == "name":
            query = query.order_by(Tool.name)
        elif sort == "price":
            query = query.outerjoin(
                PricingTier, 
                and_(
                    PricingTier.tool_id == Tool.id,
                    PricingTier.is_current == True
                )
            ).order_by(PricingTier.monthly_price.asc())
        elif sort == "rating":
            query = query.outerjoin(
                ReviewAggregate,
                ReviewAggregate.tool_id == Tool.id
            ).order_by(ReviewAggregate.avg_rating.desc())
        elif sort == "trending":
            query = query.order_by(
                Tool.query_count.desc(),
                Tool.last_queried_at.desc()
            )
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_tool(db: Session, tool_id: int):
        return db.query(Tool).filter(Tool.id == tool_id).first()

    @staticmethod
    def get_alternatives(
        db: Session,
        tool_id: int,
        min_similarity: float = 50.0,
        limit: int = 10
    ):
        # This is a simplified version - in a real app, you'd calculate similarity
        # based on features, pricing, category, etc.
        tool = ToolService.get_tool(db, tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
            
        # Get tools in the same category
        similar_tools = db.query(Tool).filter(
            Tool.category_id == tool.category_id,
            Tool.id != tool_id,
            Tool.is_active == True
        ).limit(limit).all()
        
        # Add mock similarity scores
        return [{
            **t.to_dict(),
            "similarity_score": min(100, 60 + (40 * (i / (len(similar_tools) or 1)))),
            "match_basis": "category"
        } for i, t in enumerate(similar_tools)]

    @staticmethod
    def get_pricing(db: Session, tool_id: int, include_history: bool = False):
        tool = ToolService.get_tool(db, tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
            
        current_pricing = db.query(PricingTier).filter(
            PricingTier.tool_id == tool_id,
            PricingTier.is_current == True
        ).all()
        
        result = {
            "current_pricing": [p.to_dict() for p in current_pricing]
        }
        
        if include_history:
            # In a real app, you'd have historical pricing data
            result["pricing_history"] = []
            
        return result

    @staticmethod
    def get_reviews(db: Session, tool_id: int):
        reviews = db.query(ReviewAggregate).filter(
            ReviewAggregate.tool_id == tool_id
        ).all()
        
        if not reviews:
            return {
                "avg_rating": 0,
                "total_reviews": 0,
                "sources": [],
                "rating_breakdown": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
            }
            
        total_rating = sum(r.avg_rating for r in reviews)
        avg_rating = total_rating / len(reviews) if reviews else 0
        total_reviews = sum(r.total_reviews for r in reviews)
        
        # Aggregate rating breakdown
        rating_breakdown = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for review in reviews:
            if review.rating_breakdown:
                for k, v in review.rating_breakdown.items():
                    if k in rating_breakdown:
                        rating_breakdown[k] += v
        
        return {
            "avg_rating": round(avg_rating, 2),
            "total_reviews": total_reviews,
            "sources": [r.to_dict() for r in reviews],
            "rating_breakdown": rating_breakdown
        }

    @staticmethod
    def compare_tools(db: Session, tool_ids: List[int]):
        tools = db.query(Tool).filter(Tool.id.in_(tool_ids)).all()
        
        if len(tools) != len(tool_ids):
            found_ids = {t.id for t in tools}
            missing = set(tool_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tools not found: {missing}"
            )
            
        # Get common and unique features
        features = db.query(Feature).filter(
            Feature.tool_id.in_(tool_ids)
        ).all()
        
        # Group features by tool
        tool_features = {t_id: set() for t_id in tool_ids}
        for f in features:
            tool_features[f.tool_id].add(f.feature_name)
            
        # Find common and unique features
        all_features = set()
        for f_set in tool_features.values():
            all_features.update(f_set)
            
        common_features = set.intersection(*tool_features.values()) if tool_features else set()
        unique_features = {
            t_id: list(features - common_features)
            for t_id, features in tool_features.items()
        }
        
        # Get pricing info
        pricing = {}
        for t_id in tool_ids:
            tiers = db.query(PricingTier).filter(
                PricingTier.tool_id == t_id,
                PricingTier.is_current == True
            ).order_by(PricingTier.monthly_price).all()
            
            if tiers:
                pricing[t_id] = {
                    "cheapest": min(t.monthly_price or float('inf') for t in tiers),
                    "tiers": [t.to_dict() for t in tiers]
                }
            else:
                pricing[t_id] = {"cheapest": None, "tiers": []}
        
        # Get review info
        reviews = {}
        for t_id in tool_ids:
            revs = db.query(ReviewAggregate).filter(
                ReviewAggregate.tool_id == t_id
            ).all()
            
            if revs:
                avg = sum(r.avg_rating for r in revs) / len(revs)
                reviews[t_id] = {
                    "avg_rating": round(avg, 2),
                    "total_reviews": sum(r.total_reviews for r in revs)
                }
            else:
                reviews[t_id] = {"avg_rating": 0, "total_reviews": 0}
        
        # Get integration info
        integrations = {}
        for t_id in tool_ids:
            count = db.query(Integrations).filter(
                Integrations.tool_id == t_id
            ).count()
            integrations[t_id] = count
            
        return {
            "tools": {t.id: t.to_dict() for t in tools},
            "common_features": list(common_features),
            "unique_features": {
                t_id: features 
                for t_id, features in unique_features.items() 
                if features
            },
            "pricing": pricing,
            "reviews": reviews,
            "integration_counts": integrations
        }