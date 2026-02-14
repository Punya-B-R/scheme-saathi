"""
RAG service for semantic scheme search using ChromaDB.
Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings - no API key, no rate limits.
Loads schemes from JSON, builds vector DB on first run, loads from disk on restarts.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.data_loader import (
    load_schemes_from_json,
    prepare_scheme_text_for_embedding,
)

logger = logging.getLogger(__name__)

# Backend root (app/services -> app -> backend)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(settings.get_chroma_path(BACKEND_ROOT))
MODEL_NAME = "all-MiniLM-L6-v2"


class RAGService:
    """Vector database service for government scheme semantic search."""

    COLLECTION_NAME = "government_schemes"
    BATCH_SIZE = 256  # sentence-transformers handles large batches fine

    def __init__(self) -> None:
        self.schemes: List[Dict[str, Any]] = []
        self._client: Any = None
        self._collection: Any = None
        self._model: Any = None
        self._init()

    def _init(self) -> None:
        try:
            # Load sentence transformer model
            logger.info("Loading sentence transformer model: %s...", MODEL_NAME)
            self._model = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully")

            # Load schemes from JSON
            schemes_path = settings.get_schemes_path(BACKEND_ROOT)
            self.schemes = load_schemes_from_json(str(schemes_path))
            logger.info("Loaded %s schemes", len(self.schemes))

            if not self.schemes:
                logger.warning("No schemes loaded; RAG search will return empty results.")
                return

            # Initialize ChromaDB with persistent storage
            self._initialize_vector_db()
        except Exception as e:
            logger.error("RAGService init failed: %s", e, exc_info=True)
            raise

    def _initialize_vector_db(self) -> None:
        """Create ChromaDB client, collection, and embed schemes on first run."""
        try:
            os.makedirs(CHROMA_PATH, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

            existing_count = self._collection.count()

            # If already populated, skip re-embedding
            if existing_count > 0:
                logger.info(
                    "ChromaDB already has %s schemes. Skipping embedding. Loading from disk.",
                    existing_count,
                )
                return

            # First run - need to embed all schemes
            logger.info(
                "First run: embedding %s schemes. This will take a few minutes...",
                len(self.schemes),
            )

            total = len(self.schemes)
            added = 0

            for i in range(0, total, self.BATCH_SIZE):
                batch = self.schemes[i : i + self.BATCH_SIZE]
                ids: List[str] = []
                texts: List[str] = []
                metadatas: List[Dict[str, Any]] = []

                for scheme in batch:
                    scheme_id = scheme.get("scheme_id") or ""
                    if not scheme_id:
                        continue

                    text = prepare_scheme_text_for_embedding(scheme)
                    text = (text[:8000] if text else "")  # Chroma doc length limit

                    eligibility = scheme.get("eligibility_criteria") or {}
                    if not isinstance(eligibility, dict):
                        eligibility = {}
                    state = eligibility.get("state") or "All India"
                    if isinstance(state, list):
                        state = ", ".join(str(s) for s in state)

                    ids.append(str(scheme_id))
                    texts.append(text)
                    metadatas.append({
                        "scheme_name": str(scheme.get("scheme_name", ""))[:200],
                        "category": str(scheme.get("category", ""))[:200],
                        "state": str(state or "All India")[:200],
                        "occupation": str(
                            eligibility.get("occupation", "any") or "any"
                        )[:200],
                    })

                if not ids:
                    continue

                # Generate embeddings locally - fast, no API calls
                embeddings = self._model.encode(
                    texts,
                    batch_size=64,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                embeddings_list = embeddings.tolist()

                self._collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings_list,
                    metadatas=metadatas,
                )

                added += len(ids)
                logger.info(
                    "Embedded %s/%s schemes (%.1f%%)",
                    added,
                    total,
                    100.0 * added / total,
                )

            logger.info(
                "ChromaDB initialized successfully with %s schemes. Saved to disk at %s",
                added,
                CHROMA_PATH,
            )
        except Exception as e:
            logger.error("ChromaDB initialization failed: %s", e)
            raise

    def filter_schemes_by_eligibility(
        self, schemes: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Hard filter schemes based on extracted user context.
        Remove schemes that clearly don't match user's eligibility.
        """
        if not user_context or not schemes:
            return schemes

        filtered = []
        user_state = (user_context.get("state") or "").strip().lower()
        user_occupation = (user_context.get("occupation") or "").strip().lower()
        user_caste = (user_context.get("caste_category") or "").strip().lower()
        user_gender = (user_context.get("gender") or "").strip().lower()

        for scheme in schemes:
            eligibility = scheme.get("eligibility_criteria") or {}
            if not isinstance(eligibility, dict):
                filtered.append(scheme)
                continue

            scheme_state = (eligibility.get("state") or "All India").strip().lower()
            scheme_occupation = (eligibility.get("occupation") or "any").strip().lower()
            scheme_gender = (eligibility.get("gender") or "any").strip().lower()
            scheme_caste = (eligibility.get("caste_category") or "any").strip().lower()

            # ── STATE FILTER ──
            if user_state and user_state not in ("unknown", "any", ""):
                all_india_keywords = ["all india", "all states", "national", "central"]
                is_all_india = any(kw in scheme_state for kw in all_india_keywords)
                matches_state = user_state in scheme_state or scheme_state in user_state
                if not is_all_india and not matches_state:
                    continue

            # ── OCCUPATION FILTER ──
            occupation_mismatches = {
                "farmer": ["student", "entrepreneur", "employee"],
                "student": ["farmer", "senior citizen"],
                "senior citizen": ["student", "farmer", "entrepreneur"],
                "entrepreneur": ["student", "farmer"],
            }
            if user_occupation and user_occupation not in ("unknown", "any", ""):
                if scheme_occupation not in ("any", "all", ""):
                    mismatches = occupation_mismatches.get(user_occupation, [])
                    if any(m in scheme_occupation for m in mismatches):
                        continue

            # ── GENDER FILTER ──
            if user_gender and user_gender not in ("unknown", "any"):
                if scheme_gender not in ("any", "all", ""):
                    if user_gender == "male" and "female" in scheme_gender:
                        continue
                    if user_gender == "female" and scheme_gender == "male":
                        continue

            # ── CASTE FILTER ──
            general_castes = ["any", "all", "general", ""]
            if user_caste and user_caste not in ("unknown", "any"):
                if scheme_caste not in general_castes:
                    if user_caste in general_castes:
                        continue
                    if user_caste not in scheme_caste and scheme_caste not in user_caste:
                        continue

            filtered.append(scheme)

        removed = len(schemes) - len(filtered)
        if removed > 0:
            logger.info("Hard filtered %d schemes that don't match user eligibility", removed)
        return filtered

    def search_schemes(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for schemes. Returns list of scheme dicts with match_score.
        Applies hard eligibility filter when user_context is provided.
        """
        top_k = top_k or settings.TOP_K_SCHEMES
        query = (query or "").strip() if query is not None else ""
        if not query:
            logger.warning("search_schemes called with empty query")
            return []

        try:
            logger.info("DEBUG RAG 1 - Total schemes loaded: %s", len(self.schemes))
            logger.info(
                "DEBUG RAG 2 - Collection count: %s",
                self._collection.count() if self._collection else "NO COLLECTION",
            )

            if not self._collection or self._collection.count() == 0:
                logger.warning("ChromaDB empty or not initialized")
                return []

            # Build enhanced query string
            enhanced_query = query.strip()
            if user_context:
                parts: List[str] = []
                if user_context.get("occupation") and str(user_context.get("occupation", "")).lower() not in ("unknown", "any", ""):
                    parts.append(str(user_context["occupation"]))
                if user_context.get("state") and str(user_context.get("state", "")).lower() not in ("unknown", "any", "all india", ""):
                    parts.append(str(user_context["state"]))
                if user_context.get("caste_category") and str(user_context.get("caste_category", "")).lower() not in ("unknown", "any", ""):
                    parts.append(str(user_context["caste_category"]))
                if user_context.get("age"):
                    parts.append(str(user_context["age"]))
                if parts:
                    enhanced_query = f"{enhanced_query} {' '.join(parts)}"

            logger.info("DEBUG RAG 3 - Query: %s", enhanced_query)
            logger.info("DEBUG RAG 4 - User context: %s", user_context)

            # Embed the query locally
            query_embedding = self._model.encode(
                [enhanced_query],
                convert_to_numpy=True,
            ).tolist()

            # Search ChromaDB with manual embedding
            fetch_k = min(top_k * 3, 30, self._collection.count() or 1)
            if fetch_k < 1:
                return []

            results = self._collection.query(
                query_embeddings=query_embedding,
                n_results=fetch_k,
                include=["metadatas", "distances", "documents"],
            )

            raw_count = len(results["ids"][0]) if results and results.get("ids") and results["ids"][0] else 0
            logger.info("DEBUG RAG 5 - Results before threshold filter: %s", raw_count)

            matched_schemes: List[Dict[str, Any]] = []
            scheme_by_id = {str(s.get("scheme_id", "")): s for s in self.schemes if s.get("scheme_id")}
            threshold = settings.SIMILARITY_THRESHOLD

            if results and results.get("ids") and len(results["ids"][0]) > 0:
                for scheme_id, distance in zip(
                    results["ids"][0],
                    results["distances"][0],
                ):
                    scheme = scheme_by_id.get(str(scheme_id))
                    if not scheme:
                        continue

                    # Cosine distance → similarity score (0-1)
                    match_score = max(0.0, 1.0 - float(distance))

                    if match_score >= threshold:
                        scheme_copy = dict(scheme)
                        scheme_copy["match_score"] = round(match_score, 4)
                        matched_schemes.append(scheme_copy)

            matched_schemes.sort(key=lambda s: s.get("match_score", 0), reverse=True)
            logger.info("DEBUG RAG 6 - Results after threshold filter: %s", len(matched_schemes))

            # Apply hard eligibility filter
            if user_context:
                matched_schemes = self.filter_schemes_by_eligibility(
                    matched_schemes, user_context
                )
            logger.info("DEBUG RAG 7 - Results after eligibility filter: %s", len(matched_schemes))

            return matched_schemes[:top_k]
        except Exception as e:
            logger.error("Search error: %s", e, exc_info=True)
            return []

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Return a single scheme by id or None if not found."""
        for s in self.schemes:
            if str(s.get("scheme_id", "")) == str(scheme_id):
                return s
        return None

    def get_total_schemes(self) -> int:
        """Return number of loaded schemes."""
        return len(self.schemes)

    def get_categories(self) -> List[str]:
        """Return sorted list of unique categories."""
        return sorted({s.get("category") for s in self.schemes if s.get("category")})

    def check_health(self) -> bool:
        """Return True if vector DB is usable."""
        try:
            if not self._model:
                return False
            if not self._collection:
                return False
            self._collection.count()
            return True
        except Exception as e:
            logger.error("RAG health check failed: %s", e)
            return False


# Global singleton (initializes on first import)
rag_service = RAGService()
