"""
Stage 10 News Extraction & Semantic Structuring Package.
"""

from cse.news.cache import NewsCache
from cse.news.injection_guard import (
    PromptInjectionGuard,
    is_suspicious_text,
    sanitize_text,
    wrap_untrusted_input,
)
from cse.news.llm_extract import classify_news, extract, extract_event, extract_news
from cse.news.offline import (
    OfflineEventExtractor,
    classify,
    classify_offline,
    extract_offline,
    predict_offline,
)
from cse.news.schema import (
    STRUCTURED_EVENT_JSON_SCHEMA,
    ElectionStage,
    EventCategory,
    ExpectedDirection,
    NewsExtraction,
    NewsItemInput,
    StructuredEventOutput,
    validate_structured_event_dict,
)

__all__ = [
    "NewsExtraction",
    "NewsItemInput",
    "StructuredEventOutput",
    "EventCategory",
    "ElectionStage",
    "ExpectedDirection",
    "STRUCTURED_EVENT_JSON_SCHEMA",
    "validate_structured_event_dict",
    "sanitize_text",
    "is_suspicious_text",
    "wrap_untrusted_input",
    "PromptInjectionGuard",
    "NewsCache",
    "extract_event",
    "extract_news",
    "extract",
    "classify_news",
    "extract_offline",
    "classify_offline",
    "classify",
    "predict_offline",
    "OfflineEventExtractor",
    "calculate_car",
    "CARCalculator",
    "map_to_trading_day",
    "init_db",
    "insert_news",
    "get_all_news",
    "get_aspi_range",
    "insert_aspi_prices",
    "EmbeddingEngine",
    "SimilarityIndex",
    "find_similar",
    "PriorCalculator",
    "get_prior_calculator",
    "ProximityCalculator",
    "get_proximity_calculator",
    "EnhancedExtractor",
    "get_enhanced_extractor",
    "extract_enhanced",
    "FeatureVector",
    "NewsFeatureBuilder",
    "build_features",
]

from cse.news.car_calculator import (
    CARCalculator,
    calculate_car,
    map_to_trading_day,
)
from cse.news.embedder import EmbeddingEngine
from cse.news.enhanced_extractor import (
    EnhancedExtractor,
    extract_enhanced,
    get_enhanced_extractor,
)
from cse.news.feature_builder import (
    FeatureVector,
    NewsFeatureBuilder,
    build_features,
)
from cse.news.historical_db import (
    get_all_news,
    get_aspi_range,
    init_db,
    insert_aspi_prices,
    insert_news,
)
from cse.news.prior_calculator import PriorCalculator, get_prior_calculator
from cse.news.proximity_calculator import (
    ProximityCalculator,
    get_proximity_calculator,
)
from cse.news.similarity import SimilarityIndex, find_similar


