from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(String(128), unique=True, index=True, nullable=False)
    headline = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    source_domain = Column(String(128), nullable=True)
    source_tier = Column(Integer, default=3)
    published_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    event_family = Column(String(64), nullable=True)  # Policy, Arrest, Other
    event_subtype = Column(String(64), nullable=True)
    relevance_score = Column(Float, default=0.0)
    verification_status = Column(String(32), default="Unverified")

class VerificationLog(Base):
    __tablename__ = "verification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=True)
    query_url = Column(String(1024), nullable=True)
    claim_summary = Column(Text, nullable=False)
    verdict = Column(String(64), nullable=False)  # Confirmed, Partially Corroborated, Unverified, Contradicted
    confidence_score = Column(Float, default=0.0)
    matched_evidence_json = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventEntity(Base):
    __tablename__ = "event_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    event_family = Column(String(64), nullable=False)  # Government Policy or Political Arrest
    event_subtype = Column(String(128), nullable=False)
    normalized_event_id = Column(String(64), nullable=False)
    parent_event_id = Column(String(64), nullable=True)
    cluster_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)
    event_date = Column(String(32), nullable=False)
    announcement_date = Column(String(32), nullable=True)
    market_reaction_date = Column(String(32), nullable=True)
    metadata_json = Column(Text, nullable=True)

def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
