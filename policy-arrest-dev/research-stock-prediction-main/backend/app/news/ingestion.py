from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import SessionLocal, NewsArticle, init_db
from backend.app.core.logging import logger
from backend.app.news.providers import NewsProviders
from backend.app.news.classifier import NewsClassifier

class NewsIngestionService:
    """Orchestrates news collection, deduplication, classification, and persistence."""

    def __init__(self):
        init_db()
        self.provider = NewsProviders()
        self.classifier = NewsClassifier()

    def run_ingestion(self) -> int:
        """Polls active news sources and inserts new unique articles."""
        raw_articles = self.provider.fetch_rss_feeds()
        # Also poll NewsAPI if configured
        api_articles = self.provider.fetch_newsapi()
        all_raw = raw_articles + api_articles

        if not all_raw:
            logger.info("No incoming articles retrieved during news poll.")
            return 0

        inserted_count = 0
        db: Session = SessionLocal()
        try:
            for art in all_raw:
                # Check if news_id already exists
                existing = db.query(NewsArticle).filter(NewsArticle.news_id == art["news_id"]).first()
                if existing:
                    continue

                # Classify article
                event_family, event_subtype, relevance = self.classifier.classify(
                    art["headline"], art.get("summary", "")
                )

                new_record = NewsArticle(
                    news_id=art["news_id"],
                    headline=art["headline"],
                    summary=art.get("summary", ""),
                    content=art.get("content", ""),
                    source_name=art["source_name"],
                    source_url=art["source_url"],
                    source_domain=art["source_domain"],
                    source_tier=art.get("source_tier", 3),
                    published_at=art.get("published_at", datetime.utcnow()),
                    retrieved_at=datetime.utcnow(),
                    event_family=event_family,
                    event_subtype=event_subtype,
                    relevance_score=relevance,
                    verification_status="Unverified"
                )
                db.add(new_record)
                inserted_count += 1

            db.commit()
            logger.info(f"News ingestion completed: {inserted_count} new articles added to database.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during news ingestion: {e}")
        finally:
            db.close()

        return inserted_count

    def get_latest_news(self, limit: int = 50, family: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve stored articles ordered by published date descending."""
        db: Session = SessionLocal()
        try:
            q = db.query(NewsArticle)
            if family:
                q = q.filter(NewsArticle.event_family == family)
            articles = q.order_by(desc(NewsArticle.published_at)).limit(limit).all()

            results = []
            for a in articles:
                results.append({
                    "news_id": a.news_id,
                    "headline": a.headline,
                    "summary": a.summary,
                    "source_name": a.source_name,
                    "source_url": a.source_url,
                    "source_domain": a.source_domain,
                    "source_tier": a.source_tier,
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                    "retrieved_at": a.retrieved_at.isoformat() if a.retrieved_at else None,
                    "event_family": a.event_family,
                    "event_subtype": a.event_subtype,
                    "relevance_score": a.relevance_score,
                    "verification_status": a.verification_status
                })
            return results
        finally:
            db.close()
