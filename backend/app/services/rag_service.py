"""
RAG service for semantic scheme search using ChromaDB.
Loads schemes from JSON, builds vector DB, and provides search with optional user context.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.utils.data_loader import (
    load_schemes_from_json,
    prepare_scheme_text_for_embedding,
)

logger = logging.getLogger(__name__)

# Backend root (app/services -> app -> backend)
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class RAGService:
    """Vector database service for government scheme semantic search."""

    COLLECTION_NAME = "government_schemes"
    BATCH_SIZE = 100

    def __init__(self) -> None:
        self._client = None
        self._collection = None
        self.schemes: List[Dict[str, Any]] = []
        self._chroma_path: Optional[Path] = None
        self._initialized = False
        self._init()

    def _init(self) -> None:
        try:
            chroma_path = settings.get_chroma_path(BACKEND_ROOT)
            chroma_path.mkdir(parents=True, exist_ok=True)
            self._chroma_path = chroma_path

            schemes_path = settings.get_schemes_path(BACKEND_ROOT)
            logger.info("Loading schemes from %s", schemes_path)
            self.schemes = load_schemes_from_json(str(schemes_path))

            if not self.schemes:
                logger.warning("No schemes loaded; RAG search will return empty results.")
                self._initialized = True
                return

            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Indian government schemes"},
            )

            if self._collection.count() == 0:
                logger.info("Vector DB is empty. Initializing...")
                self._initialize_vector_db()
            else:
                count = self._collection.count()
                logger.info("Vector DB loaded with %s schemes", count)

            self._initialized = True
        except Exception as e:
            logger.error("RAGService init failed: %s", e, exc_info=True)
            self.schemes = []
            self._initialized = True

    def _initialize_vector_db(self) -> None:
        """Load scheme texts and add to ChromaDB in batches."""
        if not self.schemes or not self._collection:
            return

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for s in self.schemes:
            sid = s.get("scheme_id") or ""
            if not sid:
                continue
            ids.append(sid)
            doc = prepare_scheme_text_for_embedding(s)
            documents.append(doc[:8000] if doc else "")  # Chroma doc length limit

            elig = s.get("eligibility_criteria") or {}
            if not isinstance(elig, dict):
                elig = {}
            state = (elig.get("state") or "All India")[:200]
            occupation = (elig.get("occupation") or "any")[:200]

            metadatas.append({
                "scheme_name": (s.get("scheme_name") or "")[:200],
                "category": (s.get("category") or "")[:200],
                "state": state,
                "occupation": occupation,
                "quality_score": int(s.get("data_quality_score", 0)),
            })

        total_batches = (len(ids) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        for i in range(0, len(ids), self.BATCH_SIZE):
            batch_ids = ids[i : i + self.BATCH_SIZE]
            batch_docs = documents[i : i + self.BATCH_SIZE]
            batch_meta = metadatas[i : i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            self._collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
            )
            logger.info("Added batch %s/%s", batch_num, total_batches)

        logger.info("Successfully loaded %s schemes into vector DB", len(ids))

    def _enhance_query(self, query: str, user_context: Optional[Dict[str, Any]]) -> str:
        """Append user context to query for better targeting."""
        if not user_context:
            return query.strip()
        parts = [query.strip()]
        if user_context.get("occupation") and str(user_context.get("occupation")).lower() != "unknown":
            parts.append(f"occupation: {user_context['occupation']}")
        if user_context.get("state") and str(user_context.get("state")).lower() not in ("unknown", "any", "all india", ""):
            parts.append(f"state: {user_context['state']}")
        if user_context.get("age"):
            parts.append(f"age: {user_context['age']}")
        return " | ".join(parts)

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
        if not self.schemes or not self._collection:
            return []

        top_k = top_k or settings.TOP_K_SCHEMES
        enhanced_query = self._enhance_query(query, user_context)

        try:
            n_results = min(top_k * 3, 30, self._collection.count() or 1)
            if n_results < 1:
                return []

            results = self._collection.query(
                query_texts=[enhanced_query],
                n_results=n_results,
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.error("ChromaDB search failed: %s", e)
            return []

        ids = results.get("ids", [[]])
        distances = results.get("distances", [[]])
        if not ids or not ids[0]:
            return []

        scheme_by_id = {s.get("scheme_id"): s for s in self.schemes if s.get("scheme_id")}
        threshold = settings.SIMILARITY_THRESHOLD
        out: List[Dict[str, Any]] = []

        for sid, dist in zip(ids[0], (distances[0] if distances else [])):
            scheme = scheme_by_id.get(sid)
            if not scheme:
                continue
            match_score = max(0.0, 1.0 - (float(dist) / 2.0))
            if match_score < threshold:
                continue
            scheme = dict(scheme)
            scheme["match_score"] = round(match_score, 4)
            out.append(scheme)

        out.sort(key=lambda s: s.get("match_score", 0), reverse=True)

        if user_context:
            out = self.filter_schemes_by_eligibility(out, user_context)

        return out[:top_k]

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Return a single scheme by id or None if not found."""
        for s in self.schemes:
            if s.get("scheme_id") == scheme_id:
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


# Global singleton (initializes on first import)
rag_service = RAGService()
