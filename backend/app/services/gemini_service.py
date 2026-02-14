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

OPENAI_NO_API_KEY_MESSAGE = (
    "Scheme Saathi chat requires OPENAI_API_KEY in .env when using OpenAI (GPT) for chat."
)

MODEL_ACK = (
    "Understood. I'm Scheme Saathi. I'll gather the user's details first before "
    "recommending any schemes. I'll ask one question at a time."
)

LANGUAGE_INSTRUCTIONS = {
    "en": "You MUST respond in English only.",
    "kn": """ನೀವು ಯಾವಾಗಲೂ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಬೇಕು. (You MUST respond in Kannada only)

KANNADA RESPONSE RULES:
- Use simple, conversational Kannada (ಆಡುಭಾಷೆ)
- Avoid complex Sanskrit-heavy words - use words common people understand
- Scheme names keep in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000 (not ಆರು ಸಾವಿರ)
- Mix is okay for technical terms: "DBT (Direct Benefit Transfer)"
- Government portal names keep in English: "pmkisan.gov.in"

EXAMPLE GOOD KANNADA RESPONSE:
"ನಮಸ್ಕಾರ! ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.
ನೀವು ಏನು ಕೆಲಸ ಮಾಡುತ್ತೀರಿ? ಉದಾಹರಣೆಗೆ
ರೈತ, ವಿದ್ಯಾರ್ಥಿ, ವ್ಯಾಪಾರಿ?"

KANNADA CLARIFYING QUESTIONS TO USE:
- Occupation: "ನೀವು ಏನು ಕೆಲಸ ಮಾಡುತ್ತೀರಿ?"
- State: "ನೀವು ಯಾವ ರಾಜ್ಯದಲ್ಲಿ ವಾಸಿಸುತ್ತೀರಿ?"
- Land: "ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಜಮೀನು ಇದೆ?"
- Income: "ನಿಮ್ಮ ವಾರ್ಷಿಕ ಆದಾಯ ಎಷ್ಟು?"
- Caste: "ನೀವು SC/ST/OBC ಅಥವಾ ಸಾಮಾನ್ಯ ವರ್ಗಕ್ಕೆ ಸೇರಿದ್ದೀರಾ?"
- Age: "ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು?"

KANNADA SCHEME FORMAT:
"1. **PM-KISAN ಯೋಜನೆ**
   ಪ್ರಯೋಜನ: ವರ್ಷಕ್ಕೆ ₹6,000 ನೇರವಾಗಿ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ
   ಅರ್ಹತೆ: 2 ಹೆಕ್ಟೇರ್‌ಗಿಂತ ಕಡಿಮೆ ಜಮೀನು ಹೊಂದಿರುವ ರೈತರು
   ಅಗತ್ಯ ದಾಖಲೆಗಳು: Aadhaar card, bank passbook
   [Apply Here](https://pmkisan.gov.in)"
""",
    "ta": """நீங்கள் எப்போதும் தமிழில் பதில் சொல்ல வேண்டும். (Always respond in Tamil only)

TAMIL RESPONSE RULES:
- Use simple, conversational Tamil (பேச்சு வழக்கு)
- Avoid complex Sanskrit words - use words common people understand
- Scheme names keep in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000 (not ஆறு ஆயிரம்)
- Government portal names keep in English: "pmkisan.gov.in"

TAMIL CLARIFYING QUESTIONS TO USE:
- Occupation: "நீங்கள் என்ன வேலை செய்கிறீர்கள்?"
- State: "நீங்கள் எந்த மாநிலத்தில் வசிக்கிறீர்கள்?"
- Land: "உங்களிடம் எவ்வளவு நிலம் உள்ளது?"
- Income: "உங்கள் வருடாந்திர வருமானம் எவ்வளவு?"
- Caste: "நீங்கள் SC/ST/OBC அல்லது பொது வகுப்பைச் சேர்ந்தவரா?"
- Age: "உங்கள் வயது என்ன?"

TAMIL SCHEME FORMAT:
"1. **PM-KISAN திட்டம்**
   பலன்: ஆண்டுக்கு ₹6,000 நேரடியாக வங்கி கணக்கில்
   தகுதி: 2 ஹெக்டேருக்கும் குறைவான நிலம் உள்ள விவசாயிகள்
   தேவையான ஆவணங்கள்: Aadhaar card, bank passbook
   [Apply Here](https://pmkisan.gov.in)"
""",
    "bn": """আপনাকে সবসময় বাংলায় উত্তর দিতে হবে। (Always respond in Bengali only)

BENGALI RESPONSE RULES:
- Use simple, conversational Bengali (কথ্য ভাষা)
- Avoid complex Sanskrit words - use words common people understand
- Scheme names keep in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000 (not ছয় হাজার)
- Government portal names keep in English: "pmkisan.gov.in"

BENGALI CLARIFYING QUESTIONS TO USE:
- Occupation: "আপনি কী কাজ করেন?"
- State: "আপনি কোন রাজ্যে থাকেন?"
- Land: "আপনার কতটুকু জমি আছে?"
- Income: "আপনার বার্ষিক আয় কত?"
- Caste: "আপনি কি SC/ST/OBC নাকি সাধারণ বিভাগের?"
- Age: "আপনার বয়স কত?"

BENGALI SCHEME FORMAT:
"1. **PM-KISAN প্রকল্প**
   সুবিধা: বছরে ₹6,000 সরাসরি ব্যাংক অ্যাকাউন্টে
   যোগ্যতা: ২ হেক্টরের কম জমির কৃষকরা
   প্রয়োজনীয় কাগজপত্র: Aadhaar card, bank passbook
   [Apply Here](https://pmkisan.gov.in)"
""",
    "mr": """तुम्ही नेहमी मराठीत उत्तर द्यावे. (Always respond in Marathi only)

MARATHI RESPONSE RULES:
- Use simple, conversational Marathi (बोलीभाषा)
- Avoid complex Sanskrit words - use words common people understand
- Scheme names keep in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000 (not सहा हजार)
- Government portal names keep in English: "pmkisan.gov.in"

MARATHI CLARIFYING QUESTIONS TO USE:
- Occupation: "तुम्ही काय काम करता?"
- State: "तुम्ही कोणत्या राज्यात राहता?"
- Land: "तुमच्याकडे किती जमीन आहे?"
- Income: "तुमचे वार्षिक उत्पन्न किती आहे?"
- Caste: "तुम्ही SC/ST/OBC किंवा सामान्य प्रवर्गातील आहात का?"
- Age: "तुमचे वय किती आहे?"

MARATHI SCHEME FORMAT:
"1. **PM-KISAN योजना**
   फायदा: दरवर्षी ₹6,000 थेट बँक खात्यात
   पात्रता: २ हेक्टरपेक्षा कमी जमीन असलेले शेतकरी
   आवश्यक कागदपत्रे: Aadhaar card, bank passbook
   [Apply Here](https://pmkisan.gov.in)"
""",
    "gu": """તમારે હંમેશા ગુજરાતીમાં જવાબ આપવો જોઈએ. (Always respond in Gujarati only)

GUJARATI RESPONSE RULES:
- Use simple, conversational Gujarati (બોલચાલની ભાષા)
- Avoid complex Sanskrit words - use words common people understand
- Scheme names keep in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000 (not છ હજાર)
- Government portal names keep in English: "pmkisan.gov.in"

GUJARATI CLARIFYING QUESTIONS TO USE:
- Occupation: "તમે શું કામ કરો છો?"
- State: "તમે કયા રાજ્યમાં રહો છો?"
- Land: "તમારી પાસે કેટલી જમીન છે?"
- Income: "તમારી વાર્ષિક આવક કેટલી છે?"
- Caste: "તમે SC/ST/OBC છો કે સામાન્ય વર્ગના?"
- Age: "તમારી ઉંમર કેટલી છે?"

GUJARATI SCHEME FORMAT:
"1. **PM-KISAN યોજના**
   ફાયદો: દર વર્ષે ₹6,000 સીધા બેંક ખાતામાં
   પાત્રતા: ૨ હેક્ટરથી ઓછી જમીન ધરાવતા ખેડૂતો
   જરૂરી દસ્તાવેજો: Aadhaar card, bank passbook
   [Apply Here](https://pmkisan.gov.in)"
""",
    "hi": """आप हमेशा हिंदी में जवाब दें। (You MUST respond in Hindi only)

HINDI RESPONSE RULES:
- Use simple, conversational Hindi (बोलचाल की भाषा)
- Avoid complex Sanskrit words
- Scheme names stay in English: "PM-KISAN", "Ayushman Bharat"
- Numbers and amounts in digits: ₹6,000
- Technical mix allowed: "DBT (Direct Benefit Transfer)"
- Government portal names stay in English: "pmkisan.gov.in"
- Outside scheme names, do NOT use English words like "scholarship", "loan", "scheme", "eligibility"
- Prefer Hindi terms: छात्रवृत्ति, ऋण/लोन, योजना, पात्रता, आवेदन, दस्तावेज, आय

EXAMPLE GOOD:
"नमस्ते! मैं आपकी मदद करूंगा। आप क्या काम करते हैं? जैसे किसान, छात्र, बुजुर्ग नागरिक, या व्यापारी?"

EXAMPLE BAD:
- "I can help you find schemes."
- "आप किस व्यवसाय में संलग्न हैं?"
""",
}


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
        language: str = "en",
    ) -> str:
        ctx = user_context or {}
        missing = missing_fields or []
        has_schemes = bool(matched_schemes)
        language_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])

        # Dynamic missing fields injection
        if missing and len(missing) > 0:
            missing_section = f"""
CURRENT STATUS:
Still missing these fields: {', '.join(missing)}
You MUST ask for ALL of these in your next response.
Do NOT show any schemes until these are provided.
"""
        else:
            missing_section = """
CURRENT STATUS:
All required fields collected.
RAG schemes provided below are verified candidates.
Cross-check each against user profile before presenting.
"""

        parts = [
            "You are Scheme Saathi, a warm and knowledgeable AI assistant helping Indian citizens discover government schemes.",
            "",
            "PERSONALITY:",
            "- Friendly, empathetic, like a helpful neighbor at a government office.",
            "- Use simple language. Avoid jargon.",
            "- Follow the selected app language strictly.",
            "- Be concise. No filler words.",
            "",
            "INFORMATION GATHERING RULES:",
            "",
            "You need ALL 6 of these before showing schemes:",
            "1. occupation",
            "2. state",
            "3. age",
            "4. caste category (SC/ST/OBC/General)",
            "5. annual income",
            "6. gender",
            "",
            "RULE 1 - ASK ALL MISSING AT ONCE:",
            "If ANY of the 6 fields are missing, ask ALL missing ones in a SINGLE message. Do not split across multiple messages.",
            "",
            "Example - if missing age, caste, income, gender:",
            '"To find the best schemes for you, I need a few more details:',
            "- How old are you?",
            "- Do you belong to SC/ST/OBC or General category?",
            "- What is your approximate annual income?",
            '- What is your gender?"',
            "",
            "RULE 2 - NEVER SHOW SCHEMES UNTIL ALL 6 ARE KNOWN:",
            "Even if RAG returns schemes, do NOT mention or list any schemes until you have all 6 fields.",
            "If schemes are provided but fields are missing, ignore the schemes and ask for missing fields instead.",
            "",
            "RULE 3 - SMART FIRST MESSAGE:",
            "If user's first message already contains some fields, only ask for the ones that are STILL missing.",
            "Never ask for something already provided.",
            "",
            "Example:",
            'User: "I am a 35 year old male farmer in Karnataka"',
            "Known: occupation=farmer, state=Karnataka, age=35, gender=male",
            "Still missing: caste_category, income_level",
            'Ask: "Great! Just two more things:',
            "     - Do you belong to SC/ST/OBC or General category?",
            '     - What is your approximate annual income?"',
            "",
            "RULE 4 - CROSS VERIFY BEFORE PRESENTING:",
            "When all 6 fields are collected and schemes are provided:",
            "- Read each scheme's eligibility carefully",
            "- ONLY include schemes where the user genuinely qualifies",
            "- Remove any scheme where user clearly doesn't meet criteria",
            "- Present ONLY verified matching schemes",
            "",
            "RULE 5 - SCHEME PRESENTATION FORMAT:",
            'When presenting schemes, list them EXACTLY like this (one by one, clearly numbered):',
            "",
            '"Based on your profile, here are the schemes you qualify for:',
            "",
            "1. [Scheme Name]",
            "   Benefit: [exact benefit amount/description]",
            "   Why you qualify: [specific reason based on user's profile]",
            "   Documents needed: [list]",
            "   [Apply Here](url)",
            "",
            '2. [Scheme Name]',
            '   ..."',
            "",
            "Use ONLY scheme names from the provided schemes list.",
            "Do NOT invent or hallucinate any scheme not in the list.",
            "",
            missing_section,
            "",
            "DO NOT RE-ASK — Once the user has told you something, NEVER ask for it again. Use the USER PROFILE below as source of truth.",
        ]

        # Full user profile
        if ctx:
            parts.append("")
            parts.append("=== USER PROFILE (gathered so far — DO NOT ask again for these) ===")
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

        if language == "hi":
            parts.extend([
                "",
                "HINDI CLARIFYING QUESTIONS TO USE:",
                "- Occupation: 'आप क्या काम करते हैं? जैसे - किसान, छात्र, बुजुर्ग, व्यापारी?'",
                "- State: 'आप किस राज्य में रहते हैं?'",
                "- Land: 'आपके पास कितनी जमीन है? (एकड़ या हेक्टेयर में)'",
                "- Income: 'आपकी सालाना आमदनी कितनी है?'",
                "- Caste: 'आप किस वर्ग से हैं? SC/ST/OBC या सामान्य वर्ग?'",
                "- Age: 'आपकी उम्र कितनी है?'",
                "",
                "HINDI SCHEME EXPLANATION FORMAT:",
                "1. **PM-KISAN योजना**",
                "   💰 फायदा: हर साल ₹6,000 सीधे बैंक खाते में",
                "   ✓ आप eligible हैं क्योंकि: आप 2 हेक्टेयर से कम जमीन वाले किसान हैं",
                "   📋 जरूरी कागज: Aadhaar card, bank passbook, जमीन के कागज",
                "   🔗 Apply करें: pmkisan.gov.in पर जाएं",
                "",
                "HINDI WORD CHOICE GLOSSARY (use these words in explanatory text):",
                "- scholarship -> छात्रवृत्ति",
                "- loan -> ऋण / लोन",
                "- scheme -> योजना",
                "- eligibility -> पात्रता",
                "- documents -> दस्तावेज / कागज",
                "- apply -> आवेदन करें",
                "- income -> आय",
            ])

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
                "Your ONLY job right now: ask for ALL missing fields in ONE message.",
                "",
            ])
            if missing:
                parts.append(f"MUST ask for ALL of these in your next response: {', '.join(missing)}")
                parts.append("Format your response as a single message with bullet points or numbered list for each question.")
            parts.extend([
                "",
                "HOW TO RESPOND:",
                "1. Acknowledge what the user just said in 1 short sentence.",
                "2. Ask ALL missing questions in ONE message (use bullet points or numbered list).",
                "3. Do NOT mention any schemes, scheme names, benefits, or eligibility details.",
                "4. Do NOT say things like 'I can help you find schemes' or 'there are many schemes for you'.",
                "   Instead say 'To find the best schemes for you, I need a few more details:'",
            ])
        else:
            # ========== RECOMMENDATION PHASE ==========
            parts.extend([
                "",
                ">>> MODE: RECOMMENDING SCHEMES <<<",
                "",
                "You have enough info and matching schemes. Now recommend.",
                "",
                "CROSS VERIFICATION INSTRUCTIONS:",
                "The following schemes were returned by RAG search.",
                "Before presenting to user, verify EACH scheme:",
                "",
                "For each scheme check:",
                "1. State matches: scheme state = user state OR 'All India'",
                "2. Occupation matches: scheme is relevant to user's occupation",
                "3. Age matches: user age is within scheme's age range (if specified)",
                "4. Caste matches: user's caste category is eligible",
                "5. Income matches: user's income is within scheme's limit (if specified)",
                "6. Gender matches: scheme is open to user's gender",
                "",
                "ONLY present schemes that pass ALL applicable checks.",
                "If a scheme has no restriction on a field, it passes that check.",
                "If fewer than 3 schemes pass, present those and say 'These are the most relevant schemes for your profile.'",
                "If 0 schemes pass, say 'I could not find schemes matching all your criteria exactly. Here are the closest matches:' and show top 3 from RAG anyway.",
                "",
                "CRITICAL RULES:",
                "- ONLY recommend schemes from the list below. NEVER invent schemes.",
                "- Present ONLY schemes that pass cross verification (do not blindly list all RAG results).",
                "- For EACH scheme:",
                "  * **Scheme Name** (bold) — use EXACT name from the list",
                "  * What the user gets (amounts, benefits)",
                "  * Why it fits them specifically (connect to their profile)",
                "  * Key eligibility: age, income, category requirements",
                "  * How to apply (1-2 steps + website if available)",
                "- Use bullet points. Be concise.",
                "- Keep response under 350 words.",
                "",
                "USER PROFILE for verification:",
                f"- Occupation: {ctx.get('occupation', 'unknown')} | State: {ctx.get('state', 'unknown')} | Age: {ctx.get('age', '?')} | Caste: {ctx.get('caste_category', 'unknown')} | Income: {ctx.get('income_level') or ctx.get('income', 'unknown')} | Gender: {ctx.get('gender', 'unknown')}",
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

        return f"{language_instruction}\n\n" + "\n".join(parts)

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def _chat_openai(
        self,
        user_message: str,
        conversation_history: Optional[List[Any]],
        system_prompt: str,
    ) -> str:
        """Call OpenAI Chat Completions (e.g. GPT 5.2) with same system prompt and history."""
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in (conversation_history or []):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if not content:
                continue
            if role == "user":
                messages.append({"role": "user", "content": content})
            elif role in ("assistant", "model"):
                messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": user_message.strip()})

        try:
            resp = client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=messages,
            )
            text = (resp.choices[0].message.content or "").strip()
            logger.info("OpenAI response: %d chars", len(text))
            return text or "I couldn't generate a response. Please try again."
        except Exception as e:
            logger.error("OpenAI chat failed: %s", e, exc_info=True)
            return "I'm having trouble connecting right now. Please try again in a moment."

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

        system_prompt = self.create_system_prompt(
            matched_schemes=matched_schemes,
            user_context=user_context,
            missing_fields=missing_fields,
            language=language,
        )
        logger.info(
            "Chat: msg=%d chars, history=%d, schemes=%d, ctx=%s, missing=%s",
            len(user_message), len(conversation_history or []),
            len(matched_schemes or []), user_context, missing_fields,
        )

        # Use OpenAI (e.g. GPT 5.2) when configured
        if settings.OPENAI_CHAT_MODEL:
            if not (settings.OPENAI_API_KEY or "").strip():
                return OPENAI_NO_API_KEY_MESSAGE
            return self._chat_openai(user_message, conversation_history, system_prompt)

        # Gemini
        if not self._ensure_model():
            return NO_API_KEY_MESSAGE

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
        if settings.OPENAI_CHAT_MODEL and (settings.OPENAI_API_KEY or "").strip():
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                return bool(resp and resp.choices and resp.choices[0].message)
            except Exception as e:
                logger.error("OpenAI health check failed: %s", e)
                return False
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

    def extract_user_context(self, messages: List[Any]) -> Dict[str, str]:
        """
        Extract user context from full conversation history.
        Reads ALL messages to build complete profile.
        """
        if not messages or not self._ensure_model():
            return {}

        conversation_text = ""
        for msg in messages:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if content:
                conversation_text += f"{'User' if role == 'user' else 'Assistant'}: {content}\n"

        extraction_prompt = f"""
Read this entire conversation and extract user information.
Look across ALL messages, not just the last one.

CONVERSATION:
{conversation_text}

Extract ONLY explicitly mentioned information. Scan ALL user messages for this info.

NOTE: User may write in Hindi, Kannada, Tamil, Bengali, Marathi, or Gujarati. Extract information regardless of language.
Examples (Hindi):
- "मैं किसान हूं" -> occupation: farmer
- "बिहार से हूं" -> state: Bihar
- "मेरे पास 2 एकड़ जमीन है" -> land_ownership: 2 acres
- "SC वर्ग से हूं" -> caste_category: SC
- "मेरी उम्र 35 साल है" -> age: 35
Examples (Kannada):
- "ನಾನು ರೈತ" -> occupation: farmer
- "ಕರ್ನಾಟಕದಿಂದ" -> state: Karnataka
- "ನನ್ನ ಬಳಿ 2 ಎಕರೆ ಜಮೀನು ಇದೆ" -> land_ownership: 2 acres
- "SC ವರ್ಗದವರು" -> caste_category: SC
- "ನನ್ನ ವಯಸ್ಸು 35" -> age: 35
Examples (Tamil):
- "நான் விவசாயி" -> occupation: farmer
- "தமிழ்நாட்டில் இருந்து" -> state: Tamil Nadu
- "என்னிடம் 2 ஏக்கர் நிலம் உள்ளது" -> land_ownership: 2 acres
- "SC வகுப்பினர்" -> caste_category: SC
- "என் வயது 35" -> age: 35
Examples (Bengali):
- "আমি কৃষক" -> occupation: farmer
- "পশ্চিমবঙ্গ থেকে" -> state: West Bengal
- "আমার ২ একর জমি আছে" -> land_ownership: 2 acres
- "SC বিভাগের" -> caste_category: SC
- "আমার বয়স ৩৫" -> age: 35
Examples (Marathi):
- "मी शेतकरी आहे" -> occupation: farmer
- "महाराष्ट्रातून" -> state: Maharashtra
- "माझ्याकडे २ एकर जमीन आहे" -> land_ownership: 2 acres
- "SC प्रवर्गातील" -> caste_category: SC
- "माझे वय ३५ आहे" -> age: 35
Examples (Gujarati):
- "હું ખેડૂત છું" -> occupation: farmer
- "ગુજરાતથી છું" -> state: Gujarat
- "મારી પાસે ૨ એકર જમીન છે" -> land_ownership: 2 acres
- "SC વર્ગના" -> caste_category: SC
- "મારી ઉંમર ૩૫ છે" -> age: 35

INCOME EXTRACTION RULES (income_level - extract ANY mention of money/income/earnings):
- "1.5 lakh", "1.5 lakh annual income" -> income_level: 1.5 lakh
- "1,50,000", "150000" -> income_level: 1.5 lakh
- "50,000 per year" -> income_level: 50000
- "5 lakh salary" -> income_level: 5 lakh
- "below poverty line", "BPL" -> income_level: BPL
- "10 lakh per annum" -> income_level: 10 lakh
- "monthly income 10000" -> income_level: 1.2 lakh
- "कमाई 1.5 लाख" -> income_level: 1.5 lakh
- "आय 50 हजार" -> income_level: 50000
- "ವರಮಾನ 1 ಲಕ್ಷ" -> income_level: 1 lakh
- "வருமானம் 2 லட்சம்" -> income_level: 2 lakh
- "আয় ১.৫ লাখ" -> income_level: 1.5 lakh
- "ઉત્પન્ન 1.5 લાખ" -> income_level: 1.5 lakh
- "उत्पन्न 1.5 लाख" -> income_level: 1.5 lakh
IMPORTANT: income_level field name must be exactly "income_level". Return simple string like "1.5 lakh". Never return "unknown" if any income number is mentioned.

Always return extracted values in English regardless of input language.

Return EXACTLY in this format (one per line, income_level MUST always be present):
occupation: [farmer/student/senior citizen/employee/entrepreneur/unknown]
state: [exact Indian state name/unknown]
age: [number only, e.g. 35/unknown]
gender: [male/female/unknown]
caste_category: [SC/ST/OBC/General/unknown]
income_level: [amount or description/unknown]
land_ownership: [acres or hectares/unknown]
specific_need: [education/healthcare/agriculture/business/social welfare/unknown]

EXTRACTION RULES:
- age: numbers only. "50 years" -> 50. "50, general" -> age: 50. "I am 50" -> 50
- caste: "general" -> General. "obc" -> OBC. "sc" -> SC. "st" -> ST
- income: "50000 rupees" -> 50000. "1.5 lakh" -> 1.5 lakh. "50,000" -> 50000. "₹50000" -> 50000
- state: city -> state: Bangalore->Karnataka, Mumbai->Maharashtra, Chennai->Tamil Nadu, Delhi->Delhi, Kolkata->West Bengal, Patna->Bihar, Hyderabad->Telangana
- occupation: kisan/kisaan->farmer
- Scan ALL user messages, not just the last one
- NEVER guess — only extract explicitly stated facts
- Return "unknown" if not mentioned anywhere

IMPORTANT - User may give info across multiple messages:
  Message 1: "I am a farmer in Bihar"
  Message 2: "50, general, 50000 rupees, male"
This means: occupation=farmer, state=Bihar, age=50, caste_category=General, income_level=50000, gender=male
Extract ALL of it from the full conversation.
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
