# app/services/analytics_service.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from collections import defaultdict

from app.models.tool import Tool
from app.models.category import Category
from app.models.pricing import PricingTier
from app.database.models.integration import Integration

class AnalyticsService:
    @staticmethod
    def get_pricing_trends(
        db: Session,
        category: Optional[str] = None,
        period: str = "12m"
    ) -> Dict[str, Any]:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "3m":
            start_date = end_date - timedelta(days=90)
        elif period == "6m":
            start_date = end_date - timedelta(days=180)
        else:  # 12m
            start_date = end_date - timedelta(days=365)
            
        # Query pricing history (simplified - would need a pricing history table)
        query = db.query(
            extract('year', PricingTier.effective_from).label('year'),
            extract('month', PricingTier.effective_from).label('month'),
            func.avg(PricingTier.monthly_price).label('avg_price'),
            func.count(PricingTier.id).label('count')
        ).filter(
            PricingTier.effective_from >= start_date,
            PricingTier.effective_from <= end_date,
            PricingTier.monthly_price.isnot(None)
        )
        
        if category:
            query = query.join(Tool).join(Category).filter(
                or_(
                    Category.name == category,
                    Category.slug == category
                )
            )
            
        results = query.group_by(
            'year', 'month'
        ).order_by(
            'year', 'month'
        ).all()
        
        # Format results
        return {
            "period": period,
            "category": category,
            "data": [
                {
                    "year": int(year),
                    "month": int(month),
                    "avg_price": float(avg_price) if avg_price else None,
                    "count": int(count)
                }
                for year, month, avg_price, count in results
            ]
        }

    @staticmethod
    def get_category_stats(db: Session) -> Dict[str, Any]:
        # Get tool count by category
        category_stats = db.query(
            Category.name,
            Category.slug,
            func.count(Tool.id).label('tool_count'),
            func.avg(ReviewAggregate.avg_rating).label('avg_rating')
        ).outerjoin(
            Tool, Category.id == Tool.category_id
        ).outerjoin(
            ReviewAggregate, Tool.id == ReviewAggregate.tool_id
        ).group_by(
            Category.id
        ).all()
        
        # Get price ranges by category
        price_stats = db.query(
            Category.name,
            func.min(PricingTier.monthly_price).label('min_price'),
            func.avg(PricingTier.monthly_price).label('avg_price'),
            func.max(PricingTier.monthly_price).label('max_price')
        ).join(
            Tool, Category.id == Tool.category_id
        ).join(
            PricingTier, and_(
                PricingTier.tool_id == Tool.id,
                PricingTier.is_current == True,
                PricingTier.monthly_price.isnot(None)
            )
        ).group_by(
            Category.id
        ).all()
        
        # Combine results
        price_stats_dict = {
            name: {"min_price": min_p, "avg_price": float(avg_p) if avg_p else None, "max_price": max_p}
            for name, min_p, avg_p, max_p in price_stats
        }
        
        return {
            "categories": [
                {
                    "name": name,
                    "slug": slug,
                    "tool_count": count,
                    "avg_rating": float(rating) if rating else None,
                    **price_stats_dict.get(name, {})
                }
                for name, slug, count, rating in category_stats
            ]
        }

    @staticmethod
    def get_tool_stats(db: Session, tool_id: int) -> Dict[str, Any]:
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            return None
            
        # Get basic stats
        stats = {
            "tool_id": tool.id,
            "tool_name": tool.name,
            "query_count": tool.query_count,
            "last_queried": tool.last_queried_at.isoformat() if tool.last_queried_at else None
        }
        
        # Get pricing stats
        pricing_stats = db.query(
            func.count(PricingTier.id).label('tier_count'),
            func.min(PricingTier.monthly_price).label('min_price'),
            func.avg(PricingTier.monthly_price).label('avg_price'),
            func.max(PricingTier.monthly_price).label('max_price')
        ).filter(
            PricingTier.tool_id == tool_id,
            PricingTier.is_current == True
        ).first()
        
        stats.update({
            "pricing": {
                "tier_count": pricing_stats.tier_count,
                "min_price": float(pricing_stats.min_price) if pricing_stats.min_price else None,
                "avg_price": float(pricing_stats.avg_price) if pricing_stats.avg_price else None,
                "max_price": float(pricing_stats.max_price) if pricing_stats.max_price else None
            }
        })
        
        # Get review stats
        review_stats = db.query(
            func.count(ReviewAggregate.id).label('source_count'),
            func.avg(ReviewAggregate.avg_rating).label('avg_rating'),
            func.sum(ReviewAggregate.total_reviews).label('total_reviews')
        ).filter(
            ReviewAggregate.tool_id == tool_id
        ).first()
        
        stats.update({
            "reviews": {
                "source_count": review_stats.source_count or 0,
                "avg_rating": float(review_stats.avg_rating) if review_stats.avg_rating else None,
                "total_reviews": review_stats.total_reviews or 0
            }
        })
        
        # Get feature stats
        feature_stats = db.query(
            func.count(Feature.id).label('total_features'),
            func.avg(case([(Feature.is_available == True, 1)], else_=0)).label('availability_ratio')
        ).filter(
            Feature.tool_id == tool_id
        ).first()
        
        stats.update({
            "features": {
                "total": feature_stats.total_features or 0,
                "availability_ratio": float(feature_stats.availability_ratio) if feature_stats.availability_ratio is not None else 0
            }
        })
        
        # Get integration stats
        integration_stats = db.query(
            func.count(Integration.id).label('total_integrations'),
            func.count(func.distinct(Integration.integration_type)).label('integration_types')
        ).filter(
            Integration.tool_id == tool_id
        ).first()
        
        stats.update({
            "integrations": {
                "total": integration_stats.total_integrations or 0,
                "types": integration_stats.integration_types or 0
            }
        })
        
        return stats

    @staticmethod
    def get_integration_graph(db: Session) -> Dict[str, Any]:
        # Get all integrations
        integrations = db.query(Integration).all()
        
        # Create nodes and edges
        node_ids = set()
        edges = []
        
        for integration in integrations:
            # Add tool nodes
            node_ids.add((integration.tool_id, integration.tool.name))
            node_ids.add((integration.integrates_with, integration.integrated_tool.name))
            
            # Add edge
            edges.append({
                "source": integration.tool_id,
                "target": integration.integrates_with,
                "type": integration.integration_type,
                "is_official": integration.is_official
            })
        
        # Create nodes list with unique IDs
        nodes = [{"id": node_id, "name": name} for node_id, name in node_ids]
        
        return {
            "nodes": nodes,
            "edges": edges
        }