from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import math
import logging

from app.database.models.tool import Tool
from app.database.models.feature import ToolFeature
from app.database.models.pricing import PricingTier
from app.database.models.review import ReviewAggregate
from app.database.models.integration import Integration

logger = logging.getLogger(__name__)

class ToolAnalyticsService:
    @staticmethod
    def calculate_similarity_score(db: Session, tool_id_a: int, tool_id_b: int) -> float:
        """
        Calculate similarity score between two tools (0-100)
        """
        # Get tools data
        tool_a = db.query(Tool).filter(Tool.id == tool_id_a).first()
        tool_b = db.query(Tool).filter(Tool.id == tool_id_b).first()
        
        if not tool_a or not tool_b:
            return 0.0

        # 1. Feature overlap
        features_a = {f.feature_id for f in tool_a.features}
        features_b = {f.feature_id for f in tool_b.features}
        
        common_features = len(features_a.intersection(features_b))
        total_features = len(features_a.union(features_b))
        feature_score = (common_features / total_features * 100) if total_features > 0 else 0

        # 2. Price similarity
        price_a = tool_a.avg_monthly_price or 0
        price_b = tool_b.avg_monthly_price or 0
        
        if price_a == 0 and price_b == 0:
            price_score = 100  # Both are free
        else:
            price_diff = abs(price_a - price_b)
            max_price = max(price_a, price_b) or 1  # Avoid division by zero
            price_score = (1 - price_diff / max_price) * 100

        # 3. Category match
        category_score = 100 if tool_a.category_id == tool_b.category_id else 0

        # 4. Integration overlap
        integrations_a = {i.id for i in tool_a.integrations}
        integrations_b = {i.id for i in tool_b.integrations}
        
        common_integrations = len(integrations_a.intersection(integrations_b))
        total_integrations = len(integrations_a.union(integrations_b)) or 1
        integration_score = (common_integrations / total_integrations) * 100

        # 5. Review similarity
        rating_a = tool_a.avg_rating or 0
        rating_b = tool_b.avg_rating or 0
        rating_diff = abs(rating_a - rating_b)
        review_score = (1 - rating_diff / 5) * 100  # Assuming 5-star rating scale

        # 6. Weighted final score
        similarity = (
            feature_score * 0.4 +
            price_score * 0.2 +
            category_score * 0.15 +
            integration_score * 0.15 +
            review_score * 0.1
        )

        return round(similarity, 2)

    @staticmethod
    def calculate_trending_score(tool: Tool) -> float:
        """
        Calculate trending score for a tool
        """
        if not tool.last_queried_at:
            return 0.0
            
        # 1. Recency multiplier (7-day half-life)
        hours_since_query = (datetime.now(timezone.utc) - tool.last_queried_at).total_seconds() / 3600
        recency_multiplier = math.exp(-hours_since_query / 168)  # 168 hours = 7 days
        
        # 2. Popularity
        popularity = (tool.query_count or 0) * recency_multiplier
        
        # 3. Quality boost
        total_reviews = tool.review_aggregate.total_reviews if tool.review_aggregate else 0
        avg_rating = tool.review_aggregate.average_rating if tool.review_aggregate else 0
        quality_multiplier = (avg_rating / 5.0) * math.log(total_reviews + 1)
        
        # 4. Final score
        trending_score = popularity * quality_multiplier
        return trending_score

    @classmethod
    def update_tool_query_stats(cls, db: Session, tool_id: int) -> bool:
        """
        Update query stats for a tool and recalculate trending score
        """
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return False
            
        # Update stats
        tool.query_count = (tool.query_count or 0) + 1
        tool.last_queried_at = datetime.now(timezone.utc)
        
        # Recalculate trending score
        tool.trending_score = cls.calculate_trending_score(tool)
        
        db.commit()
        return True

    @classmethod
    def get_tool_recommendations(
        cls, 
        db: Session, 
        tool_id: int, 
        limit: int = 10,
        min_similarity: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Get recommended tools based on similarity
        """
        source_tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not source_tool:
            return []
            
        # Get all candidate tools in the same category
        candidates = db.query(Tool).filter(
            Tool.category_id == source_tool.category_id,
            Tool.id != tool_id,
            Tool.is_active == True
        ).all()
        
        recommendations = []
        max_query_count = max((t.query_count or 0 for t in candidates), default=1)
        
        for candidate in candidates:
            # Calculate similarity score
            score = cls.calculate_similarity_score(db, tool_id, candidate.id)
            
            if score >= min_similarity:
                # Add popularity boost (0-10 points)
                popularity_boost = ((candidate.query_count or 0) / max_query_count) * 10
                final_score = min(100, score + popularity_boost)
                
                recommendations.append({
                    'tool_id': candidate.id,
                    'name': candidate.name,
                    'score': round(final_score, 2),
                    'price_tier': candidate.avg_monthly_price
                })
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit results per price tier for diversity
        price_tiers = {}
        final_recommendations = []
        
        for rec in recommendations:
            tier = 'free' if rec['price_tier'] == 0 else 'premium'
            price_tiers[tier] = price_tiers.get(tier, 0) + 1
            
            if price_tiers[tier] <= 3:  # Max 3 per tier
                final_recommendations.append(rec)
                if len(final_recommendations) >= limit:
                    break
        
        return final_recommendations

    @classmethod
    def detect_price_changes(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Detect and log price changes for all tools
        """
        from app.database.models.changelog import Changelog
        
        changes = []
        
        # Get all tools with multiple pricing tiers
        tools = db.query(Tool).join(PricingTier).group_by(Tool.id).having(func.count(PricingTier.id) > 1).all()
        
        for tool in tools:
            # Get current and previous pricing
            current_price = db.query(PricingTier).filter(
                PricingTier.tool_id == tool.id,
                PricingTier.is_current == True
            ).first()
            
            if not current_price:
                continue
                
            previous_price = db.query(PricingTier).filter(
                PricingTier.tool_id == tool.id,
                PricingTier.effective_to == current_price.effective_from
            ).first()
            
            if not previous_price or current_price.monthly_price == previous_price.monthly_price:
                continue
                
            # Calculate change percentage
            change_percent = 0
            if previous_price.monthly_price > 0:  # Avoid division by zero
                change_percent = ((current_price.monthly_price - previous_price.monthly_price) / 
                                previous_price.monthly_price) * 100
            
            # Log the change
            change = Changelog(
                tool_id=tool.id,
                change_type='pricing',
                old_value=str(previous_price.monthly_price),
                new_value=str(current_price.monthly_price),
                change_percent=change_percent
            )
            
            db.add(change)
            changes.append({
                'tool_id': tool.id,
                'tool_name': tool.name,
                'old_price': previous_price.monthly_price,
                'new_price': current_price.monthly_price,
                'change_percent': change_percent,
                'change_date': datetime.now(timezone.utc)
            })
        
        db.commit()
        return changes

    @classmethod
    def search_tools(
        cls,
        db: Session,
        query_string: str,
        category_id: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        features: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for tools with full-text search and filters
        """
        from sqlalchemy.sql import text
        from sqlalchemy.dialects.postgresql import TSVECTOR
        
        # Base query with full-text search
        query = db.query(
            Tool,
            func.ts_rank(
                func.to_tsvector('english', 
                    func.coalesce(Tool.name, '') + ' ' +
                    func.coalesce(Tool.description, '') + ' ' +
                    func.coalesce(Tool.tagline, '')
                ),
                func.plainto_tsquery('english', query_string)
            ).label('relevance')
        )
        
        # Apply text search condition
        query = query.filter(
            func.to_tsvector('english', 
                func.coalesce(Tool.name, '') + ' ' +
                func.coalesce(Tool.description, '') + ' ' +
                func.coalesce(Tool.tagline, '')
            ).op('@@')(func.plainto_tsquery('english', query_string))
        )
        
        # Apply filters
        if category_id:
            query = query.filter(Tool.category_id == category_id)
            
        if price_min is not None or price_max is not None:
            query = query.join(PricingTier, PricingTier.tool_id == Tool.id)
            query = query.filter(PricingTier.is_current == True)
            
            if price_min is not None:
                query = query.filter(PricingTier.monthly_price >= price_min)
            if price_max is not None:
                query = query.filter(PricingTier.monthly_price <= price_max)
        
        if features:
            # For each feature, join with ToolFeature and filter
            for i, feature in enumerate(features):
                alias = f"tf{i}"
                query = query.join(
                    ToolFeature,
                    and_(
                        ToolFeature.tool_id == Tool.id,
                        ToolFeature.feature_name == feature
                    ),
                    isouter=True
                )
            
            # Ensure at least one feature matches
            query = query.filter(or_(*[
                ToolFeature.feature_name == feature 
                for feature in features
            ]))
        
        # Execute query and format results
        results = query.order_by(text('relevance DESC')).limit(limit).all()
        
        return [{
            'tool': tool,
            'relevance': float(relevance) if relevance else 0.0
        } for tool, relevance in results]
