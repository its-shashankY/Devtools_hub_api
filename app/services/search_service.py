# app/services/search_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

from app.models.tool import Tool
from app.models.category import Category
from app.models.pricing import PricingTier
from app.models.review import ReviewAggregate
from app.models.feature import Feature

class SearchService:
    @staticmethod
    def search_tools(
        db: Session,
        query: str,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        features: Optional[List[str]] = None
    ):
        # Basic full-text search across tool name, description, and tagline
        search_terms = f"%{query}%"
        query_obj = db.query(Tool).filter(
            or_(
                Tool.name.ilike(search_terms),
                Tool.description.ilike(search_terms),
                Tool.tagline.ilike(search_terms)
            )
        )
        
        # Apply filters
        if category:
            query_obj = query_obj.join(Category).filter(
                or_(
                    Category.name.ilike(f"%{category}%"),
                    Category.slug.ilike(f"%{category}%")
                )
            )
            
        if price_min is not None or price_max is not None:
            query_obj = query_obj.join(PricingTier, and_(
                PricingTier.tool_id == Tool.id,
                PricingTier.is_current == True
            ))
            
            if price_min is not None:
                query_obj = query_obj.filter(PricingTier.monthly_price >= price_min)
            if price_max is not None:
                query_obj = query_obj.filter(PricingTier.monthly_price <= price_max)
                
        if features:
            for feature in features:
                query_obj = query_obj.join(Feature).filter(
                    Feature.feature_name.ilike(f"%{feature}%"),
                    Feature.is_available == True
                )
        
        # Order by relevance (simplified - could be enhanced with full-text search)
        query_obj = query_obj.order_by(
            Tool.query_count.desc(),
            Tool.last_queried_at.desc()
        )
        
        return query_obj.all()

    @staticmethod
    def get_trending_tools(
        db: Session,
        period: str = "7d",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        # Calculate time delta based on period
        now = datetime.utcnow()
        if period == "24h":
            delta = timedelta(days=1)
        elif period == "30d":
            delta = timedelta(days=30)
        else:  # 7d default
            delta = timedelta(days=7)
            
        time_threshold = now - delta
        
        # Simple trending algorithm: weight recent queries higher
        query = db.query(Tool).filter(
            Tool.last_queried_at >= time_threshold
        ).order_by(
            (Tool.query_count * func.coalesce(ReviewAggregate.avg_rating, 0)).desc()
        ).outerjoin(
            ReviewAggregate,
            ReviewAggregate.tool_id == Tool.id
        ).limit(limit)
        
        return [
            {
                "id": tool.id,
                "name": tool.name,
                "slug": tool.slug,
                "logo_url": tool.logo_url,
                "query_count": tool.query_count,
                "avg_rating": float(avg_rating) if (avg_rating := tool.avg_rating) is not None else None
            }
            for tool in query.all()
        ]

    @staticmethod
    def get_recently_updated(
        db: Session,
        change_type: Optional[str] = None,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        from app.models.changelog import Changelog
        
        query = db.query(Changelog).filter(
            Changelog.changed_at >= datetime.utcnow() - timedelta(days=days)
        )
        
        if change_type:
            query = query.filter(Changelog.change_type == change_type)
            
        query = query.order_by(Changelog.changed_at.desc()).limit(limit)
        
        return [
            {
                "tool_id": change.tool_id,
                "tool_name": change.tool.name,
                "change_type": change.change_type,
                "change_summary": change.change_summary,
                "changed_at": change.changed_at.isoformat()
            }
            for change in query.all()
        ]

    @staticmethod
    def get_recommendations(
        db: Session,
        tool_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        # Get the target tool
        target_tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not target_tool:
            return []
            
        # Get tools in the same category
        similar_tools = db.query(Tool).filter(
            Tool.category_id == target_tool.category_id,
            Tool.id != target_tool.id,
            Tool.is_active == True
        ).limit(limit * 2).all()  # Get more than needed to filter later
        
        # Simple scoring (in a real app, this would be more sophisticated)
        def calculate_score(tool):
            score = 0.0
            
            # Category match
            if tool.category_id == target_tool.category_id:
                score += 0.15
                
            # Price similarity (if available)
            if target_tool.pricing_tiers and tool.pricing_tiers:
                target_price = min((p.monthly_price or float('inf') for p in target_tool.pricing_tiers), default=None)
                tool_price = min((p.monthly_price or float('inf') for p in tool.pricing_tiers), default=None)
                
                if target_price and tool_price:
                    price_ratio = min(target_price, tool_price) / max(target_price, tool_price)
                    score += 0.2 * price_ratio
            
            # Feature overlap
            target_features = {f.feature_name for f in target_tool.features if f.is_available}
            tool_features = {f.feature_name for f in tool.features if f.is_available}
            common_features = target_features.intersection(tool_features)
            
            if target_features:
                feature_overlap = len(common_features) / len(target_features)
                score += 0.4 * feature_overlap
                
            # Integration overlap
            target_integrations = {i.integrates_with for i in target_tool.integrations_out}
            tool_integrations = {i.integrates_with for i in tool.integrations_out}
            common_integrations = target_integrations.intersection(tool_integrations)
            
            if target_integrations:
                integration_overlap = len(common_integrations) / len(target_integrations)
                score += 0.15 * integration_overlap
                
            # Review similarity (simplified)
            target_rating = db.query(func.avg(ReviewAggregate.avg_rating)).filter(
                ReviewAggregate.tool_id == target_tool.id
            ).scalar() or 0
                
            tool_rating = db.query(func.avg(ReviewAggregate.avg_rating)).filter(
                ReviewAggregate.tool_id == tool.id
            ).scalar() or 0
            
            rating_similarity = 1 - (abs(target_rating - tool_rating) / 5)  # Normalize to 0-1
            score += 0.1 * rating_similarity
            
            return score
            
        # Score and sort tools
        scored_tools = [
            (tool, calculate_score(tool))
            for tool in similar_tools
        ]
        
        # Sort by score descending and take top N
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "tool": {
                    "id": tool.id,
                    "name": tool.name,
                    "slug": tool.slug,
                    "logo_url": tool.logo_url,
                    "category_id": tool.category_id
                },
                "score": round(score, 2),
                "match_reasons": [
                    "Similar features" if score >= 0.2 else "",
                    "Similar pricing" if 0.1 <= score < 0.3 else "",
                    "Same category" if score >= 0.05 else ""
                ]
            }
            for tool, score in scored_tools[:limit]
        ]