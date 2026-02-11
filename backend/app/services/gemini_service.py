"""
Gemini AI service for Scheme Saathi: conversation, context extraction, and scheme-aware responses.
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

NO_API_KEY_MESSAGE = (
    "Scheme Saathi is not configured with a Gemini API key yet. "
    "Please add GEMINI_API_KEY to your .env file. "
    "Get a key from: https://makersuite.google.com/app/apikey"
)

MODEL_ACK = (
    "Understood. I'm Scheme Saathi. I'll gather the user's details first before "
    "recommending any schemes. I'll ask one question at a time."
)


class GeminiService:
    """Google Gemini integration for conversational scheme discovery."""

    def __init__(self) -> None:
        self._model = None
        self._genai = None
        try:
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "placeholder":
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
                self._genai = genai
                logger.info("Gemini initialized with model: %s", settings.GEMINI_MODEL)
            else:
                logger.warning("GEMINI_API_KEY not set.")
        except Exception as e:
            logger.error("Gemini init failed: %s", e, exc_info=True)

    def _ensure_model(self) -> bool:
        if self._model is not None:
            return True
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "placeholder":
            return False
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self._genai = genai
            return True
        except Exception as e:
            logger.error("Gemini lazy init failed: %s", e)
            return False

    # ------------------------------------------------------------------
    # System prompt builder
    # ------------------------------------------------------------------

    def create_system_prompt(
        self,
        matched_schemes: Optional[List[Dict[str, Any]]] = None,
        user_context: Optional[Dict[str, str]] = None,
        missing_fields: Optional[List[str]] = None,
    ) -> str:
        """Build system prompt with conversation flow control."""
        ctx = user_context or {}
        missing = missing_fields or []
        has_schemes = bool(matched_schemes)

        parts = [
            "You are Scheme Saathi, a warm and knowledgeable AI assistant that helps Indian citizens discover government schemes.",
            "",
            "PERSONALITY: Friendly, simple language, empathetic. Like a helpful neighbor.",
            "Respond in the same language the user writes in.",
        ]

        # What we know
        if ctx:
            parts.append("")
            parts.append("USER PROFILE (gathered so far):")
            for k, v in ctx.items():
                parts.append(f"  - {k.replace('_', ' ').title()}: {v}")

        if not has_schemes:
            # ========== GATHERING PHASE ==========
            parts.extend([
                "",
                ">>> CURRENT MODE: GATHERING INFORMATION <<<",
                "",
                "You do NOT have enough information yet. DO NOT recommend any schemes.",
                "DO NOT name any scheme. DO NOT say 'here are some schemes'. DO NOT list benefits.",
                "",
                "Your job right now: ask the user for ONE more piece of information.",
                "",
            ])
            if missing:
                # Map field names to natural questions
                field_questions = {
                    "state": "which state they are from",
                    "occupation": "what they do (student, farmer, employee, business owner, etc.)",
                    "gender": "their gender (this helps find women-specific schemes)",
                    "age": "their age",
                    "caste_category": "their category (General, SC, ST, OBC) - ask sensitively",
                }
                next_field = missing[0]
                question_hint = field_questions.get(next_field, next_field.replace("_", " "))
                parts.append(f"Ask about: {question_hint}")
                parts.append(f"(Still need: {', '.join(f.replace('_', ' ') for f in missing)})")
            parts.extend([
                "",
                "HOW TO ASK:",
                "1. First acknowledge what the user just told you (briefly).",
                "2. Then ask ONE natural question about the next missing detail.",
                "3. Keep it short (2-3 sentences max).",
                "4. Do NOT mention schemes, benefits, or eligibility at all.",
            ])
        else:
            # ========== RECOMMENDATION PHASE ==========
            parts.extend([
                "",
                ">>> CURRENT MODE: RECOMMENDING SCHEMES <<<",
                "",
                "You have enough info and matching schemes. Now recommend.",
                "",
                "RULES:",
                "- Present TOP 2-3 most relevant schemes from the list below.",
                "- For each scheme, include:",
                "  * **Scheme Name** (bold)",
                "  * What the user gets (benefits, amounts)",
                "  * Why it fits them specifically",
                "  * How to apply (1-2 key steps)",
                "  * Website link if available",
                "- Use bullet points. Be concise.",
                "- ONLY use schemes from the list below. NEVER invent anything.",
                "- If user asks follow-up, give more detail on that scheme.",
                "- If user corrects info (e.g., 'not OBC'), acknowledge and adjust.",
                "- Keep response under 350 words.",
            ])

            parts.extend(["", "=== VERIFIED MATCHING SCHEMES ==="])
            for i, s in enumerate(matched_schemes[:7], 1):
                name = s.get("scheme_name", "Unknown")
                category = s.get("category", "")

                benefits = s.get("benefits") or {}
                if isinstance(benefits, dict):
                    benefit_text = (benefits.get("summary") or benefits.get("raw_benefits_text") or "")[:300]
                else:
                    benefit_text = str(benefits)[:300]

                elig = s.get("eligibility_criteria") or {}
                if isinstance(elig, dict):
                    elig_text = (elig.get("raw_eligibility_text") or "")[:300]
                    state = elig.get("state", "All India")
                    gender = elig.get("gender", "any")
                    caste = elig.get("caste_category", "any")
                    age = elig.get("age_range", "any")
                else:
                    elig_text = ""
                    state, gender, caste, age = "All India", "any", "any", "any"

                url = s.get("source_url") or s.get("official_website") or ""

                parts.append(f"\n{i}. {name} [{category}]")
                parts.append(f"   Benefits: {benefit_text}")
                if elig_text:
                    parts.append(f"   Eligibility: {elig_text}")
                parts.append(f"   State: {state} | Gender: {gender} | Category: {caste} | Age: {age}")
                if url:
                    parts.append(f"   Website: {url}")
            parts.append("\n=== END SCHEMES ===")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Any]] = None,
        matched_schemes: Optional[List[Dict[str, Any]]] = None,
        user_context: Optional[Dict[str, str]] = None,
        missing_fields: Optional[List[str]] = None,
        language: str = "en",
    ) -> str:
        """Main conversation method."""
        if not user_message or not user_message.strip():
            return "Please send a message so I can help you."

        if not self._ensure_model():
            return NO_API_KEY_MESSAGE

        system_prompt = self.create_system_prompt(matched_schemes, user_context, missing_fields)
        logger.info(
            "Chat: msg_len=%d, history=%d, schemes=%s, ctx=%s, missing=%s",
            len(user_message),
            len(conversation_history or []),
            len(matched_schemes or []),
            user_context,
            missing_fields,
        )

        # Build Gemini history
        messages = [
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": [MODEL_ACK]},
        ]
        for msg in (conversation_history or []):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if not content:
                continue
            if role == "user":
                messages.append({"role": "user", "parts": [content]})
            elif role in ("assistant", "model"):
                messages.append({"role": "model", "parts": [content]})

        try:
            history_for_api = []
            for m in messages:
                role = m.get("role", "user")
                parts = m.get("parts", [])
                text = parts[0] if parts else ""
                if isinstance(text, dict):
                    text = text.get("text", "")
                if not text:
                    continue
                history_for_api.append({"role": role, "parts": [{"text": text}]})

            chat_session = self._model.start_chat(history=history_for_api)
            response = chat_session.send_message(user_message.strip())
            text = (response.text or "").strip()
            logger.info("Chat response: %d chars", len(text))
            return text or "I couldn't generate a response. Please try again."
        except Exception as e:
            logger.error("Chat failed: %s", e, exc_info=True)
            try:
                full_prompt = system_prompt + "\n\n"
                for msg in (conversation_history or []):
                    content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
                    role = getattr(msg, "role", None) or (msg.get("role", "") if isinstance(msg, dict) else "user")
                    full_prompt += f"{'User' if role == 'user' else 'Assistant'}: {content}\n"
                full_prompt += f"User: {user_message.strip()}\nAssistant:"
                resp = self._model.generate_content(full_prompt)
                return (resp.text or "").strip() or "I'm having trouble. Please try again."
            except Exception as e2:
                logger.error("Chat fallback failed: %s", e2)
                return "I'm having trouble connecting right now. Please try again in a moment."

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def check_health(self) -> bool:
        if not self._ensure_model():
            return False
        try:
            response = self._model.generate_content("Hello")
            return bool(response and response.text)
        except Exception as e:
            logger.error("Gemini health check failed: %s", e)
            return False

    def generate_reply(
        self,
        user_message: str,
        context_schemes: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Backward-compatible wrapper."""
        return self.chat(
            user_message=user_message,
            conversation_history=[],
            matched_schemes=context_schemes,
            language="en",
        )


gemini_service = GeminiService()
