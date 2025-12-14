# scripts/init_db.py
import logging
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import Tool, Category, PricingTier, Feature, ReviewAggregate, Integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Create categories
    categories = [
        Category(name="Version Control", slug="version-control", description="Tools for version control and code collaboration"),
        Category(name="CI/CD", slug="ci-cd", description="Continuous Integration and Continuous Deployment tools"),
        Category(name="Cloud Providers", slug="cloud-providers", description="Cloud infrastructure providers"),
    ]
    
    for category in categories:
        db.add(category)
    db.commit()
    
    # Create tools
    tools = [
        Tool(
            name="GitHub",
            slug="github",
            category_id=1,
            description="GitHub is a development platform inspired by the way you work. From open source to business, you can host and review code, manage projects, and build software alongside millions of other developers.",
            tagline="Where the world builds software",
            website_url="https://github.com",
            logo_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
            company_name="GitHub, Inc.",
            is_active=True
        ),
        # Add more tools...
    ]
    
    for tool in tools:
        db.add(tool)
    db.commit()
    
    logger.info("Database initialized with sample data")

if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)