"""Semantic Embedding and Sentiment Analysis Engine for CSE News.

Provides:
- 384-dimensional dense semantic embeddings (using sentence-transformers/all-MiniLM-L6-v2
  with resilient sklearn TF-IDF + TruncatedSVD fallback)
- Financial sentiment scoring (using ProsusAI/finbert with domain lexicon fallback)
- Persistent embedding cache in data/embedding_cache.pkl (keyed by sha256(text))
- Unit-normalized vectors for exact inner-product cosine similarity
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from cse.utils.config import find_project_root

logger = logging.getLogger("cse.news.embedder")

EMBEDDING_DIM = 384
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FINBERT_MODEL = "ProsusAI/finbert"

# Financial domain synonyms and acronym normalization for robust semantic matching
DOMAIN_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bcb\b", re.IGNORECASE), "central bank"),
    (re.compile(r"\bcbsl\b", re.IGNORECASE), "central bank"),
    (re.compile(r"\bpolicy rates?\b", re.IGNORECASE), "policy interest rate"),
    (re.compile(r"\brates?\b", re.IGNORECASE), "interest rate policy"),
    (re.compile(r"\bcuts?\b", re.IGNORECASE), "cut reduce lower"),
    (re.compile(r"\breduces?\b", re.IGNORECASE), "cut reduce lower"),
    (re.compile(r"\bhikes?\b", re.IGNORECASE), "hike increase raise"),
    (re.compile(r"\blwers?\b", re.IGNORECASE), "cut reduce lower"),
    (re.compile(r"\beff\b", re.IGNORECASE), "extended fund facility loan imf"),
    (re.compile(r"\bisbs?\b", re.IGNORECASE), "international sovereign bonds debt"),
    (re.compile(r"\bddo\b", re.IGNORECASE), "domestic debt optimization restructuring"),
    (re.compile(r"\bpresidential poll\b", re.IGNORECASE), "presidential election vote"),
    (re.compile(r"\bgeneral poll\b", re.IGNORECASE), "parliamentary general election"),
]

# Baseline corpus to seed TF-IDF vocabulary across all CSE macro-event categories
SEED_CORPUS: List[str] = [
    "central bank cuts policy interest rate sdfr slfr by 50 basis points monetary easing",
    "cb reduces interest rates to stimulate economic growth and private sector credit",
    "cbsl lowers policy corridor rate amid disinflation and currency stability",
    "central bank maintains policy interest rates citing anchored inflation expectations",
    "president dissolves parliament setting date for parliamentary general election poll",
    "election commission gazettes presidential election polling date nominations accepted",
    "imf executive board completes review of extended fund facility disbursing tranche",
    "sri lanka concludes debt restructuring agreement with official creditor committee and bondholders",
    "cabinet approved value added tax revision and national tariff reforms",
    "treasury bill auction yields decline across 3-month and 6-month maturities",
    "colombo stock exchange aspi index gains on heavy foreign institutional buying",
    "commercial bank reports record quarterly operating profit and loan book expansion",
    "protesters gather demanding political accountability and economic relief measures",
    "supreme court directs treasury on election funding allocation and legal compliance",
]


def normalize_text_domain(text: str) -> str:
    """Normalize acronyms and financial terms for semantic matching."""
    t = text.lower().strip()
    for pattern, replacement in DOMAIN_REPLACEMENTS:
        t = pattern.sub(replacement, t)
    return t


def get_default_cache_path() -> Path:
    """Resolve default embedding cache path in <project_root>/data/embedding_cache.pkl."""
    root = find_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "embedding_cache.pkl"


class SklearnTfidfSvdEmbedder:
    """Resilient 384-dimensional text embedder using TF-IDF and Truncated SVD."""

    def __init__(self, corpus: Optional[List[str]] = None) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        training_corpus = list(SEED_CORPUS)
        if corpus:
            training_corpus.extend(corpus)

        cleaned_corpus = [normalize_text_domain(doc) for doc in training_corpus]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            max_features=2500,
        )
        X = self.vectorizer.fit_transform(cleaned_corpus)

        n_features = X.shape[1]
        n_components = min(n_features - 1, min(EMBEDDING_DIM, max(10, len(training_corpus) - 1)))
        if n_components < 2:
            n_components = max(1, n_features)

        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.svd.fit(X)
        self.dim = EMBEDDING_DIM

    def embed(self, text: str) -> np.ndarray:
        """Produce unit-normalized 384-dim embedding vector."""
        clean_text = normalize_text_domain(text)
        tfidf_vec = self.vectorizer.transform([clean_text])
        svd_vec = self.svd.transform(tfidf_vec)[0]

        # Pad to exactly 384 dimensions
        out = np.zeros(self.dim, dtype=np.float32)
        n_avail = min(len(svd_vec), self.dim)
        out[:n_avail] = svd_vec[:n_avail]

        # Normalize to unit length
        norm = np.linalg.norm(out)
        if norm > 1e-12:
            out = out / norm
        else:
            out[0] = 1.0  # Fallback unit vector

        return out

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Produce unit-normalized (N, 384) matrix."""
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        clean_texts = [normalize_text_domain(t) for t in texts]
        tfidf_mat = self.vectorizer.transform(clean_texts)
        svd_mat = self.svd.transform(tfidf_mat)

        N = len(texts)
        out = np.zeros((N, self.dim), dtype=np.float32)
        n_avail = min(svd_mat.shape[1], self.dim)
        out[:, :n_avail] = svd_mat[:, :n_avail]

        # Row-wise L2 normalization
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        out = out / norms
        return out.astype(np.float32)


class LexiconSentimentAnalyzer:
    """Domain-specific financial lexicon sentiment analyzer fallback."""

    POSITIVE_WORDS = {
        "cuts", "cut", "reduce", "reduces", "reduction", "surplus", "growth",
        "expansion", "upgraded", "upgrade", "gain", "gains", "profit", "profits",
        "surge", "surges", "record", "recovery", "rebound", "approved", "approves",
        "disbursing", "disbursed", "bullish", "agreement", "agrees", "eased",
        "inflows", "stabilizes", "stabilization", "boosts", "buoyant", "consensus",
    }

    NEGATIVE_WORDS = {
        "hike", "hikes", "inflation", "deficit", "default", "defaulted", "crisis",
        "arrest", "arrested", "probe", "corruption", "protest", "protests",
        "strike", "hartal", "curfew", "drop", "drops", "loss", "losses", "fall",
        "falls", "decline", "declines", "downgrade", "downgrades", "warning",
        "suspension", "suspended", "disruption", "unrest", "debt", "rejections",
    }

    def score(self, text: str) -> Dict[str, float]:
        """Compute positive, negative, neutral, and compound scores."""
        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}

        pos_count = sum(1 for t in tokens if t in self.POSITIVE_WORDS)
        neg_count = sum(1 for t in tokens if t in self.NEGATIVE_WORDS)
        total = len(tokens)

        # Contextual check for rate cuts (rate cut is positive for equity markets)
        if "cuts" in tokens or "reduces" in tokens:
            if "rate" in tokens or "rates" in tokens:
                pos_count += 2

        if pos_count == 0 and neg_count == 0:
            return {"positive": 0.05, "negative": 0.05, "neutral": 0.90, "compound": 0.0}

        raw_pos = pos_count / (pos_count + neg_count + 1.0)
        raw_neg = neg_count / (pos_count + neg_count + 1.0)
        raw_neu = 1.0 - (raw_pos + raw_neg)

        # Normalize to sum to 1.0
        total_p = raw_pos + raw_neg + max(0.1, raw_neu)
        p = round(raw_pos / total_p, 4)
        n = round(raw_neg / total_p, 4)
        neu = round(1.0 - (p + n), 4)

        compound = round(float(np.clip(p - n, -1.0, 1.0)), 4)
        return {"positive": p, "negative": n, "neutral": neu, "compound": compound}


class EmbeddingEngine:
    """Unified embedding and financial sentiment engine with disk caching."""

    def __init__(
        self,
        cache_path: Optional[Union[str, Path]] = None,
        corpus: Optional[List[str]] = None,
        prefer_cpu: bool = True,
    ) -> None:
        self.cache_path = Path(cache_path) if cache_path else get_default_cache_path()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.prefer_cpu = prefer_cpu

        self._cache: Dict[str, np.ndarray] = self._load_cache()
        self._transformer_model: Optional[Any] = None
        self._finbert_pipeline: Optional[Any] = None
        self.model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
        self.sentiment_model_name: str = "ProsusAI/finbert"

        # Initialize embedder model with resilient fallback
        self._init_embedder(corpus)

        # Initialize sentiment analyzer with fallback
        self._init_sentiment()

    def _load_cache(self) -> Dict[str, np.ndarray]:
        """Load persistent embedding cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "rb") as f:
                    data = pickle.load(f)
                if isinstance(data, dict):
                    logger.info("Loaded %d cached embeddings from %s", len(data), self.cache_path)
                    return data
            except Exception as e:
                logger.warning("Could not read embedding cache %s (%s). Starting fresh.", self.cache_path, e)
        return {}

    def save_cache(self) -> None:
        """Persist current embedding cache to disk."""
        try:
            with open(self.cache_path, "wb") as f:
                pickle.dump(self._cache, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug("Saved %d embeddings to cache %s", len(self._cache), self.cache_path)
        except Exception as e:
            logger.warning("Failed saving embedding cache: %s", e)

    def _init_embedder(self, corpus: Optional[List[str]] = None) -> None:
        """Attempt to load sentence-transformers or fall back to sklearn SVD."""
        try:
            from sentence_transformers import SentenceTransformer
            device = "cpu" if self.prefer_cpu else None
            self._transformer_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL, device=device)
            self.model_name = SENTENCE_TRANSFORMER_MODEL
            logger.info("Successfully loaded sentence-transformers: %s", self.model_name)
            return
        except Exception as e:
            logger.debug("sentence-transformers unavailable: %s", e)

        # Fallback to sklearn TF-IDF + SVD
        logger.info("Using resilient fallback: SklearnTfidfSvdEmbedder (384 dimensions).")
        self._transformer_model = SklearnTfidfSvdEmbedder(corpus=corpus)
        self.model_name = "sklearn-tfidf-svd-fallback"

    def _init_sentiment(self) -> None:
        """Attempt to load ProsusAI/finbert pipeline or fall back to lexicon analyzer."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            device = -1 if self.prefer_cpu else 0
            tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL, local_files_only=True)
            self._finbert_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, return_all_scores=True, device=device)
            self.sentiment_model_name = FINBERT_MODEL
            logger.info("Successfully loaded FinBERT sentiment model.")
            return
        except Exception as e:
            logger.debug("FinBERT local files unavailable (%s). Using LexiconSentimentAnalyzer.", e)

        self._finbert_pipeline = LexiconSentimentAnalyzer()
        self.sentiment_model_name = "lexicon-financial-sentiment"

    def _cache_key(self, text: str) -> str:
        """Compute SHA256 digest of normalized text."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def embed(self, text: str) -> np.ndarray:
        """Generate unit-normalized 384-dimensional embedding for text.
        
        Returns
        -------
        np.ndarray
            1D array of shape (384,) with L2 norm == 1.0.
        """
        key = self._cache_key(text)
        if key in self._cache:
            return self._cache[key]

        if hasattr(self._transformer_model, "encode"):
            vec = self._transformer_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            out = vec.astype(np.float32)
        else:
            out = self._transformer_model.embed(text)

        # Ensure exact shape and normalization
        if out.shape != (EMBEDDING_DIM,):
            padded = np.zeros(EMBEDDING_DIM, dtype=np.float32)
            n = min(len(out), EMBEDDING_DIM)
            padded[:n] = out[:n]
            out = padded

        norm = np.linalg.norm(out)
        if norm > 1e-12:
            out = out / norm

        self._cache[key] = out
        return out

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate unit-normalized (N, 384) embeddings for a list of texts.
        
        Returns
        -------
        np.ndarray
            2D array of shape (len(texts), 384).
        """
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

        results: List[Optional[np.ndarray]] = [None] * len(texts)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        for idx, t in enumerate(texts):
            key = self._cache_key(t)
            if key in self._cache:
                results[idx] = self._cache[key]
            else:
                missing_indices.append(idx)
                missing_texts.append(t)

        if missing_texts:
            if hasattr(self._transformer_model, "encode"):
                batch_vecs = self._transformer_model.encode(
                    missing_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    batch_size=32,
                    show_progress_bar=False,
                ).astype(np.float32)
            else:
                batch_vecs = self._transformer_model.embed_batch(missing_texts)

            for idx, orig_idx in enumerate(missing_indices):
                vec = batch_vecs[idx]
                norm = np.linalg.norm(vec)
                if norm > 1e-12:
                    vec = vec / norm
                self._cache[self._cache_key(texts[orig_idx])] = vec
                results[orig_idx] = vec

            self.save_cache()

        matrix = np.array(results, dtype=np.float32)
        return matrix

    def sentiment(self, text: str) -> Dict[str, float]:
        """Compute sentiment scores for text.
        
        Returns
        -------
        dict
            {"positive": float, "negative": float, "neutral": float, "compound": float}
        """
        if isinstance(self._finbert_pipeline, LexiconSentimentAnalyzer):
            return self._finbert_pipeline.score(text)

        # FinBERT pipeline inference
        try:
            preds = self._finbert_pipeline(text)[0]
            scores = {item["label"].lower(): float(item["score"]) for item in preds}
            pos = round(scores.get("positive", 0.0), 4)
            neg = round(scores.get("negative", 0.0), 4)
            neu = round(scores.get("neutral", 0.0), 4)
            compound = round(pos - neg, 4)
            return {"positive": pos, "negative": neg, "neutral": neu, "compound": compound}
        except Exception as e:
            logger.warning("FinBERT inference error (%s). Falling back to lexicon.", e)
            return LexiconSentimentAnalyzer().score(text)
