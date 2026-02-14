"""
RAG service for semantic scheme search using ChromaDB.
Loads pre-computed embeddings from disk. Uses OpenAI for query embedding only.
No sentence-transformers or PyTorch at runtime - fits in 512MB Render.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from openai import OpenAI

from app.config import settings
from app.utils.data_loader import (
    load_schemes_from_json,
    prepare_scheme_text_for_embedding,
)

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(settings.get_chroma_path(BACKEND_ROOT))


class RAGService:
    """Vector database service for government scheme semantic search."""

    COLLECTION_NAME = "government_schemes"

    def __init__(self) -> None:
        self.schemes: List[Dict[str, Any]] = []
        self._client: Any = None
        self._collection: Any = None
        self._init()

    def _init(self) -> None:
        try:
            schemes_path = settings.get_schemes_path(BACKEND_ROOT)
            self.schemes = load_schemes_from_json(str(schemes_path))
            logger.info("Loaded %s schemes from JSON", len(self.schemes))

            if not self.schemes:
                logger.warning("No schemes loaded; RAG search will return empty results.")
                return

            self._initialize_vector_db()
        except Exception as e:
            logger.error("RAGService init failed: %s", e, exc_info=True)
            raise

    def _initialize_vector_db(self) -> None:
        """Load ChromaDB from disk. No embedding - pre-computed only."""
        try:
            if not os.path.exists(CHROMA_PATH):
                logger.error(
                    "ChromaDB not found at %s. Run scripts/precompute_embeddings.py locally first.",
                    CHROMA_PATH,
                )
                self._collection = None
                return

            self._client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_collection(name=self.COLLECTION_NAME)

            count = self._collection.count()
            logger.info("ChromaDB loaded from disk: %s schemes", count)

            if count == 0:
                logger.error("ChromaDB is empty! Run precompute script.")
        except Exception as e:
            logger.error("ChromaDB load failed: %s", e)
            self._collection = None

    def filter_schemes_by_eligibility(
        self, schemes: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Hard filter schemes based on extracted user context.
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

            if user_state and user_state not in ("unknown", "any", ""):
                all_india_keywords = ["all india", "all states", "national", "central"]
                is_all_india = any(kw in scheme_state for kw in all_india_keywords)
                matches_state = user_state in scheme_state or scheme_state in user_state
                if not is_all_india and not matches_state:
                    continue

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

            if user_gender and user_gender not in ("unknown", "any"):
                if scheme_gender not in ("any", "all", ""):
                    if user_gender == "male" and "female" in scheme_gender:
                        continue
                    if user_gender == "female" and scheme_gender == "male":
                        continue

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
        Semantic search for schemes. Uses OpenAI for query embedding.
        Returns list of scheme dicts with match_score.
        """
        top_k = top_k or settings.TOP_K_SCHEMES
        query = (query or "").strip() if query is not None else ""
        if not query:
            logger.warning("search_schemes called with empty query")
            return []

        if not self._collection or self._collection.count() == 0:
            logger.warning("ChromaDB empty or not initialized")
            return []

        try:
            enhanced_query = query.strip()
            if user_context:
                parts: List[str] = []
                occ = str(user_context.get("occupation", "") or "").lower()
                if occ and occ not in ("unknown", "any", ""):
                    parts.append(str(user_context["occupation"]))
                if occ == "student":
                    edu = str(user_context.get("education_level", "") or "").lower()
                    if edu and edu not in ("unknown", "any", ""):
                        parts.append(edu)
                        if edu == "undergraduate":
                            parts.append("undergraduate scholarship degree student")
                        elif edu == "postgraduate":
                            parts.append("postgraduate masters fellowship")
                        elif edu == "phd":
                            parts.append("phd doctoral research fellowship")
                if user_context.get("state") and str(user_context.get("state", "")).lower() not in ("unknown", "any", "all india", ""):
                    parts.append(str(user_context["state"]))
                if user_context.get("caste_category") and str(user_context.get("caste_category", "")).lower() not in ("unknown", "any", ""):
                    parts.append(str(user_context["caste_category"]))
                if user_context.get("age"):
                    parts.append(str(user_context["age"]))
                if parts:
                    enhanced_query = f"{enhanced_query} {' '.join(parts)}"

            api_key = (settings.OPENAI_API_KEY or "").strip()
            if not api_key or api_key == "placeholder":
                logger.error("OPENAI_API_KEY not set for query embedding")
                return []

            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=[enhanced_query],
            )
            query_embedding = response.data[0].embedding

            fetch_k = min(top_k * 3, 30, self._collection.count() or 1)
            if fetch_k < 1:
                return []

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=fetch_k,
                include=["metadatas", "distances", "documents"],
            )

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

                    match_score = max(0.0, 1.0 - float(distance))
                    if match_score >= threshold:
                        scheme_copy = dict(scheme)
                        scheme_copy["match_score"] = round(match_score, 4)
                        matched_schemes.append(scheme_copy)

            matched_schemes.sort(key=lambda s: s.get("match_score", 0), reverse=True)

            if user_context:
                matched_schemes = self.filter_schemes_by_eligibility(
                    matched_schemes, user_context
                )

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
            if not self._collection:
                return False
            self._collection.count()
            return True
        except Exception as e:
            logger.error("RAG health check failed: %s", e)
            return False


rag_service = RAGService()
