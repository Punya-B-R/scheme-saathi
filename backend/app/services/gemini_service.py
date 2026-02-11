"""
Gemini AI service for Scheme Saathi.
Builds smart system prompts based on user context + matched schemes.
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
    def __init__(self) -> None:
        self._model = None
        self._genai = None
        try:
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "placeholder":
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
                self._genai = genai
                logger.info("Gemini initialized: %s", settings.GEMINI_MODEL)
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
        ctx = user_context or {}
        missing = missing_fields or []
        has_schemes = bool(matched_schemes)

        parts = [
            "You are Scheme Saathi, a warm and knowledgeable AI assistant helping Indian citizens discover government schemes.",
            "",
            "PERSONALITY:",
            "- Friendly, empathetic, like a helpful neighbor at a government office.",
            "- Use simple language. Avoid jargon.",
            "- Respond in the same language the user writes in (Hindi/English/Hinglish).",
            "- Be concise. No filler words.",
        ]

        # Full user profile
        if ctx:
            parts.append("")
            parts.append("=== USER PROFILE (gathered so far) ===")
            label_map = {
                "state": "State",
                "occupation": "Occupation",
                "gender": "Gender",
                "age": "Age",
                "caste_category": "Category",
                "education_level": "Education Level",
                "income": "Income",
                "bpl": "Below Poverty Line",
                "disability": "Disability",
                "residence": "Residence (urban/rural)",
                "family_status": "Family Status",
            }
            for key, label in label_map.items():
                val = ctx.get(key)
                if val:
                    parts.append(f"  {label}: {val}")
            parts.append("=== END PROFILE ===")

        if not has_schemes:
            # ========== GATHERING PHASE ==========
            parts.extend([
                "",
                ">>> MODE: GATHERING INFORMATION <<<",
                "",
                "You do NOT have enough information yet.",
                "DO NOT recommend any schemes. DO NOT name any scheme.",
                "DO NOT say 'here are some schemes' or list benefits.",
                "",
                "Your ONLY job: ask ONE more piece of information.",
                "",
            ])
            if missing:
                field_questions = {
                    "state": "which state/UT they are from",
                    "occupation": "what they do (student, farmer, employee, business owner, retired, etc.)",
                    "gender": "their gender (this helps find gender-specific schemes)",
                    "age": "their age or approximate age range",
                    "caste_category": "their category (General/SC/ST/OBC/Minority) — ask politely, explain it helps find reserved schemes",
                }
                next_q = field_questions.get(missing[0], missing[0].replace("_", " "))
                parts.append(f"Next question: Ask about {next_q}")
                if len(missing) > 1:
                    parts.append(f"(Still need after this: {', '.join(f.replace('_',' ') for f in missing[1:])})")
            parts.extend([
                "",
                "HOW TO ASK:",
                "1. Briefly acknowledge what the user just told you (1 short sentence).",
                "2. Ask ONE clear question about the next missing detail.",
                "3. Max 2-3 sentences total.",
                "4. Do NOT mention schemes, benefits, or eligibility at all.",
            ])
        else:
            # ========== RECOMMENDATION PHASE ==========
            parts.extend([
                "",
                ">>> MODE: RECOMMENDING SCHEMES <<<",
                "",
                "You have enough info and matching schemes. Now recommend.",
                "",
                "CRITICAL RULES:",
                "- ONLY recommend schemes from the list below. NEVER invent schemes.",
                "- Present the TOP 2-3 most relevant schemes.",
                "- For EACH scheme:",
                "  * **Scheme Name** (bold)",
                "  * What the user gets (amounts, benefits)",
                "  * Why it fits them specifically (connect to their profile)",
                "  * Key eligibility: age, income, category requirements",
                "  * How to apply (1-2 steps + website if available)",
                "- Use bullet points. Be concise.",
                "- Keep response under 350 words.",
                "",
                "RELEVANCE CHECK — Before including a scheme, verify:",
                f"- User is: {ctx.get('occupation', 'unknown')} | {ctx.get('gender', 'unknown')} | age {ctx.get('age', '?')} | {ctx.get('caste_category', 'unknown')} | {ctx.get('state', 'unknown')}",
            ])
            if ctx.get("education_level"):
                parts.append(f"- Education: {ctx['education_level']} (do NOT suggest pre-matric schemes for college students or vice versa)")
            if ctx.get("disability") != "yes":
                parts.append("- User does NOT have a disability. Skip disability-specific schemes.")
            if ctx.get("family_status"):
                parts.append(f"- Family status: {ctx['family_status']}")
            parts.extend([
                "- If a scheme doesn't match the user's profile, SKIP IT even if it's in the list.",
                "- If user asks follow-up about a specific scheme, give full details.",
                "- If user corrects info, acknowledge and adjust.",
            ])

            # Scheme data
            parts.extend(["", "=== MATCHED SCHEMES (pre-filtered for relevance) ==="])
            for i, s in enumerate(matched_schemes[:7], 1):
                name = s.get("scheme_name", "Unknown")
                category = s.get("category", "")

                benefits = s.get("benefits") or {}
                if isinstance(benefits, dict):
                    benefit_text = (benefits.get("summary") or benefits.get("raw_benefits_text") or "")[:350]
                else:
                    benefit_text = str(benefits)[:350]

                elig = s.get("eligibility_criteria") or {}
                if isinstance(elig, dict):
                    elig_text = (elig.get("raw_eligibility_text") or "")[:350]
                    state = elig.get("state", "All India")
                    gender = elig.get("gender", "any")
                    caste = elig.get("caste_category", "any")
                    age = elig.get("age_range", "any")
                    occ = elig.get("occupation", "any")
                else:
                    elig_text, state, gender, caste, age, occ = "", "All India", "any", "any", "any", "any"

                url = s.get("source_url") or s.get("official_website") or ""

                parts.append(f"\n{i}. {name} [{category}]")
                parts.append(f"   Benefits: {benefit_text}")
                if elig_text:
                    parts.append(f"   Eligibility: {elig_text}")
                parts.append(f"   State: {state} | Gender: {gender} | Category: {caste} | Age: {age} | Occupation: {occ}")
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
        if not user_message or not user_message.strip():
            return "Please send a message so I can help you."

        if not self._ensure_model():
            return NO_API_KEY_MESSAGE

        system_prompt = self.create_system_prompt(matched_schemes, user_context, missing_fields)
        logger.info(
            "Chat: msg=%d chars, history=%d, schemes=%d, ctx=%s, missing=%s",
            len(user_message), len(conversation_history or []),
            len(matched_schemes or []), user_context, missing_fields,
        )

        # Build Gemini conversation
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
                text = m.get("parts", [""])[0]
                if isinstance(text, dict):
                    text = text.get("text", "")
                if not text:
                    continue
                history_for_api.append({"role": role, "parts": [{"text": text}]})

            chat_session = self._model.start_chat(history=history_for_api)
            response = chat_session.send_message(user_message.strip())
            text = (response.text or "").strip()
            logger.info("Response: %d chars", len(text))
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
                logger.error("Fallback failed: %s", e2)
                return "I'm having trouble connecting right now. Please try again in a moment."

    def check_health(self) -> bool:
        if not self._ensure_model():
            return False
        try:
            response = self._model.generate_content("Hello")
            return bool(response and response.text)
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return False

    def generate_reply(self, user_message: str, context_schemes=None, system_prompt=None) -> str:
        return self.chat(user_message=user_message, conversation_history=[], matched_schemes=context_schemes)


gemini_service = GeminiService()
