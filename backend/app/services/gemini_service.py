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
            "",
            "CONVERSATION FLOW (you MUST follow this strictly):",
            "",
            "STAGE 1 - GATHER INFORMATION (you MUST ask ALL of these before showing any scheme):",
            "You need to collect AT LEAST these 4 pieces of information:",
            "  1. Occupation (farmer/student/senior citizen/employee/entrepreneur/homemaker/etc.)",
            "  2. State (which Indian state they are from)",
            "  3. Type of help needed (what they are looking for):",
            "     Examples: scholarship/fee waiver, loan/credit, pension, health insurance/medical,",
            "     housing, financial assistance/money, marriage help, skill training/course,",
            "     business support/startup, employment/job, subsidy, food/nutrition, legal help, etc.",
            "  4. At least ONE of: Gender, Age, OR Caste category (SC/ST/OBC/General)",
            "",
            "After those 4 mandatory pieces, ask more if relevant:",
            "  - Gender (if not known yet)",
            "  - Age or age range",
            "  - Caste category (SC/ST/OBC/General/Minority) — ask sensitively",
            "  - Education level (if student: school/college/post-grad)",
            "  - Income level / BPL status",
            "  - Land ownership (if farmer)",
            "",
            "STAGE 2 - RECOMMEND (ONLY when you have occupation + state + type of help + 1 more detail):",
            "Show matched schemes from the provided list. Explain why each matches. Highlight key benefits.",
            "",
            "STAGE 3 - DETAIL (when user asks about a specific scheme):",
            "Give complete details, required documents, and step-by-step application process.",
            "",
            "QUESTIONING RULES (VERY IMPORTANT):",
            "- Ask ONE question at a time. Never ask 2+ questions in one message.",
            "- Question order:",
            "  (1) Occupation → 'What do you do? (student/farmer/employee/business/retired/homemaker/etc.)'",
            "  (2) State → 'Which state are you from?'",
            "  (3) Type of help → 'What kind of help are you looking for? For example: scholarship, loan, pension, financial help, health cover, housing, training, marriage assistance, etc.'",
            "  (4) Gender/Age/Caste (pick whichever is most relevant to their occupation + help type)",
            "     - For student wanting scholarship → ask caste category (many scholarships are caste-specific)",
            "     - For farmer → ask about land ownership / income",
            "     - For senior citizen → ask age",
            "     - For women-specific help → confirm gender",
            "- For caste, ask politely: 'To find category-specific schemes, may I know your category — General, SC, ST, OBC, or Minority?'",
            "- If the user already told you some info in earlier messages, DO NOT ask again. Use what you know.",
            "- If the user gave multiple details at once (e.g. 'I am a female student from Karnataka looking for scholarships'), acknowledge ALL of them and ask the next missing piece.",
            "",
            "CRITICAL RULES:",
            "- Do NOT show or name ANY scheme until you have at least: occupation + state + type of help + 1 more.",
            "- If you do NOT have a list of schemes below, you are in GATHERING mode. DO NOT name or recommend any scheme.",
            "- Never assume the user's state, gender, caste, or help type. Always ask explicitly.",
            "- Read previous messages carefully. Never re-ask something already answered.",
            "- When user mentions something like 'scholarship' or 'loan' or 'marriage' — that IS their type of help. Don't ask again.",
        ]

        # Full user profile
        if ctx:
            parts.append("")
            parts.append("=== USER PROFILE (gathered so far) ===")
            label_map = {
                "occupation": "Occupation",
                "state": "State",
                "help_type": "Type of help needed",
                "specific_need": "Specific need",
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
                "You do NOT have enough information yet to recommend schemes.",
                "DO NOT recommend any schemes. DO NOT name any scheme. DO NOT mention specific benefits.",
                "DO NOT say 'here are some schemes' or 'based on your profile' or list any scheme names.",
                "",
                "Your ONLY job right now: ask ONE more piece of information.",
                "",
            ])
            if missing:
                field_questions = {
                    "occupation": "what they do (student, farmer, employee, business owner, retired, homemaker, etc.)",
                    "state": "which state/UT they are from",
                    "help_type": "what kind of help they need — ask: 'What kind of help are you looking for? For example: scholarship, loan, pension, financial help, medical/health, housing, training, marriage assistance, employment, etc.'",
                    "gender": "their gender (this helps find gender-specific schemes)",
                    "age": "their age or approximate age range",
                    "caste_category": "their category (General/SC/ST/OBC/Minority) — ask politely, explain it helps find reserved schemes",
                }
                next_q = field_questions.get(missing[0], missing[0].replace("_", " "))
                parts.append(f"→ NEXT QUESTION TO ASK: {next_q}")
                if len(missing) > 1:
                    parts.append(f"(After this, still need: {', '.join(f.replace('_',' ') for f in missing[1:])})")
            parts.extend([
                "",
                "HOW TO RESPOND:",
                "1. Acknowledge what the user just said in 1 short sentence.",
                "   Example: 'Got it, you're a student from Karnataka.'",
                "2. Ask ONE clear, specific question about the NEXT missing detail.",
                "3. Keep your response to 2-3 sentences maximum.",
                "4. Do NOT mention any schemes, scheme names, benefits, amounts, or eligibility details.",
                "5. Do NOT say things like 'I can help you find schemes' or 'there are many schemes for you'.",
                "   Instead say 'To find the best options for you, I need a few more details.'",
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
                "RELEVANCE CHECK — Before including a scheme, verify it matches the user:",
                f"- User is: {ctx.get('occupation', 'unknown')} | {ctx.get('gender', 'unknown')} | age {ctx.get('age', '?')} | {ctx.get('caste_category', 'unknown')} | {ctx.get('state', 'unknown')}",
            ])
            if ctx.get("specific_need"):
                parts.append(f"- User specifically wants: {ctx['specific_need']}. Do NOT recommend schemes of a different type (e.g., if they want scholarship, don't show loans).")
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

    # ------------------------------------------------------------------
    # Context extraction (optional; main.py uses regex by default)
    # ------------------------------------------------------------------

    def parse_context_response(self, response_text: str) -> Dict[str, str]:
        """Parse extraction response into key-value context. Only non-empty, non-unknown."""
        context: Dict[str, str] = {}
        for line in (response_text or "").strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if value and value.lower() != "unknown":
                    context[key] = value
        return context

    def extract_user_context(self, conversation: List[Any]) -> Dict[str, str]:
        """
        Use Gemini to extract structured user context from conversation.
        Call only when conversation_history is non-empty (adds latency).
        """
        if not conversation or not self._ensure_model():
            return {}

        conv_text = ""
        for msg in conversation:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if content:
                conv_text += f"{'User' if role == 'user' else 'Assistant'}: {content}\n"

        extraction_prompt = f"""
Analyze this conversation and extract ONLY explicitly mentioned information.

Conversation:
{conv_text}

Extract these fields. Use "unknown" if not mentioned. Be VERY STRICT - only extract what is explicitly stated.

Return EXACTLY in this format (one per line):
occupation: [farmer/student/senior citizen/employee/entrepreneur/unknown]
state: [exact Indian state name/unknown]
age: [number/unknown]
gender: [male/female/unknown]
caste_category: [SC/ST/OBC/General/unknown]
income_level: [amount or description/unknown]
land_ownership: [acres or hectares/unknown]
specific_need: [education/healthcare/agriculture/business/social welfare/unknown]

RULES:
- For state: use full state name (e.g., "Karnataka" not "KA")
- For occupation: standardize to common terms
- NEVER guess or infer - only extract explicitly stated facts
- If user says "I'm from Bangalore" → state: Karnataka
- If user says "I'm a kisan" → occupation: farmer
"""
        try:
            resp = self._model.generate_content(extraction_prompt)
            text = (resp.text or "").strip()
            return self.parse_context_response(text)
        except Exception as e:
            logger.error("Context extraction failed: %s", e)
            return {}

    def generate_reply(self, user_message: str, context_schemes=None, system_prompt=None) -> str:
        return self.chat(user_message=user_message, conversation_history=[], matched_schemes=context_schemes)


gemini_service = GeminiService()
