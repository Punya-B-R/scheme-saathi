"""
FastAPI application for Scheme Saathi backend.
Comprehensive context extraction + multi-dimensional scheme filtering.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    SchemeSearchRequest,
    SchemeSearchResponse,
    SubscribeRequest,
    SubscribeResponse,
    UnsubscribeRequest,
)
from app.database import get_db, init_db
from app.chat_history import (
    append_message,
    get_or_create_chat_for_message,
)
from app.auth_router import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.utils.subscriber_db import (
    add_subscriber,
    get_all_active_subscribers,
    unsubscribe as unsubscribe_subscriber,
)
from app.services.email_service import (
    send_welcome_email,
    send_alerts_to_matching_subscribers,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered government scheme discovery for Indian citizens",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

from app.auth_router import router as auth_router
from app.chats_router import router as chats_router

app.include_router(auth_router)
app.include_router(chats_router)


# ============================================================
# 1. CONTEXT EXTRACTION ENGINE
#    Extracts every possible dimension from user text via regex.
#    Zero API calls. ~1ms per message.
# ============================================================

INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya",
    "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim",
    "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand",
    "west bengal", "delhi", "jammu and kashmir", "ladakh", "chandigarh",
    "puducherry", "andaman and nicobar",
]

STATE_DISPLAY = {s: s.title() for s in INDIAN_STATES}
STATE_DISPLAY.update({
    "delhi": "Delhi", "tamil nadu": "Tamil Nadu", "uttar pradesh": "Uttar Pradesh",
    "madhya pradesh": "Madhya Pradesh", "andhra pradesh": "Andhra Pradesh",
    "himachal pradesh": "Himachal Pradesh", "arunachal pradesh": "Arunachal Pradesh",
    "west bengal": "West Bengal", "jammu and kashmir": "Jammu and Kashmir",
})

# City → state mapping for context extraction
CITY_TO_STATE = {
    "bangalore": "Karnataka", "bengaluru": "Karnataka",
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu",
    "hyderabad": "Telangana", "secunderabad": "Telangana",
    "delhi": "Delhi", "new delhi": "Delhi",
    "kolkata": "West Bengal", "calcutta": "West Bengal",
    "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh", "varanasi": "Uttar Pradesh",
    "patna": "Bihar",
    "jaipur": "Rajasthan", "udaipur": "Rajasthan", "jodhpur": "Rajasthan",
    "ahmedabad": "Gujarat", "surat": "Gujarat", "vadodara": "Gujarat",
    "chandigarh": "Chandigarh",
    "kochi": "Kerala", "thiruvananthapuram": "Kerala", "trivandrum": "Kerala",
}

OCCUPATIONS = {
    r"\bfarmer\b|\bkisan\b|\bfarming\b|\bagricultur\w*\b|\bcrop\b|\bkhet\b|\bkheti\b": "farmer",
    r"\bstudents?\b|\bstudying\b|\bcollege\b|\buniversity\b|\bengineering\b|\bmedical\s+student\b|\bbtech\b|\bmba\b|\bschool\b|\bscholarship\b|\bclass\s+\d|\bmatric\b|\bdegree\b|\bpost.?graduate\b|\bgraduate\b|\bdiploma\b|\bphd\b": "student",
    r"\bsenior\s*citizens?\b|\bretired\b|\bold\s*age\b|\bpensioners?\b|\belderly\b|\bvridh\b|\bpension\b": "senior citizen",
    r"\bbusiness\b|\bentrepreneur\b|\bself.?employed\b|\bshop\s*keeper\b|\bstartup\b|\bmsme\b|\btrader\b|\budyami\b|\bvendor\b": "entrepreneur",
    r"\bworker\b|\blabou?r\b|\bemployee\b|\bdaily\s*wage\b|\bsalaried\b|\bjob\b|\bconstruction\s+worker\b|\bdomestic\s+worker\b": "worker",
    r"\bfisherm[ae]n\b|\bfishing\b|\bmatsyakara\b": "fisherman",
    r"\bartisan\b|\bhandicraft\b|\bweaver\b|\bpotter\b|\bvishwakarma\b|\bcarpenter\b|\bblacksmith\b": "artisan",
    r"\bhousewife\b|\bhomemaker\b|\bhouse\s*wife\b": "homemaker",
}

GENDERS = {
    r"\bfemale\b|\bwoman\b|\bwomen\b|\bgirl\b|\bmahila\b|\bmother\b|\bpregnant\b|\bwidow\b|\blady\b|\bdaughter\b|\bsister\b": "female",
    r"\bmale\b(?!\s*(?:and|or|\/)\s*female)|\bboy\b|\bson\b": "male",
}

# Gujarati state names/variants -> English (for context extraction from Gujarati input)
GUJARATI_STATE_MAP = {
    "ગુજરાત": "Gujarat", "ગુજરાતથી": "Gujarat", "ગુજરાતના": "Gujarat",
    "મહારાષ્ટ્ર": "Maharashtra", "બિહાર": "Bihar", "કર્ણાટક": "Karnataka",
    "કેરળ": "Kerala", "તમિલનાડુ": "Tamil Nadu", "રાજસ્થાન": "Rajasthan",
    "આંધ્ર પ્રદેશ": "Andhra Pradesh", "તેલંગાણા": "Telangana",
    "પંજાબ": "Punjab", "મધ્ય પ્રદેશ": "Madhya Pradesh", "ઉત્તર પ્રદેશ": "Uttar Pradesh",
    "પશ્ચિમ બંગાળ": "West Bengal", "ઓડિશા": "Odisha", "દિલ્હી": "Delhi",
    "હરિયાણા": "Haryana",
}

# Gujarati occupation patterns (regex on original text)
GUJARATI_OCCUPATION_PATTERNS = [
    (r"ખેડૂત|ખેતી|કૃષિ", "farmer"),
    (r"વિદ્યાર્થી|વિદ્યાર્થિની|શિક્ષણ", "student"),
    (r"વૃદ્ધ|વડીલ|વૃદ્ધ નાગરિક|પેન્શન", "senior citizen"),
    (r"વ્યવસાયી|ઉદ્યોગપતિ|વ્યવસાય", "entrepreneur"),
    (r"કામદાર|કર્મચારી|કામ", "worker"),
    (r"ગૃહિણી|સ્ત્રી|મહિલા", "homemaker"),
]

# Marathi state names/variants -> English (for context extraction from Marathi input)
MARATHI_STATE_MAP = {
    "महाराष्ट्र": "Maharashtra", "महाराष्ट्रातून": "Maharashtra", "महाराष्ट्रातील": "Maharashtra",
    "बिहार": "Bihar", "कर्नाटक": "Karnataka", "केरळ": "Kerala",
    "तामीळनाडू": "Tamil Nadu", "राजस्थान": "Rajasthan", "आंध्र प्रदेश": "Andhra Pradesh",
    "तेलंगणा": "Telangana", "गुजरात": "Gujarat", "पंजाब": "Punjab",
    "मध्य प्रदेश": "Madhya Pradesh", "उत्तर प्रदेश": "Uttar Pradesh",
    "पश्चिम बंगाल": "West Bengal", "ओडिशा": "Odisha", "दिल्ली": "Delhi",
    "हरियाणा": "Haryana",
}

# Marathi occupation patterns (regex on original text; Devanagari)
MARATHI_OCCUPATION_PATTERNS = [
    (r"शेतकरी|शेतकी|कृषि", "farmer"),
    (r"विद्यार्थी|विद्यार्थिनी|शिक्षण", "student"),
    (r"ज्येष्ठ|वृद्ध|ज्येष्ठ नागरिक|निवृत्तीवेतन", "senior citizen"),
    (r"व्यवसायी|उद्योजक|व्यवसाय", "entrepreneur"),
    (r"कामगार|कर्मचारी|काम", "worker"),
    (r"गृहिणी|स्त्री|महिला", "homemaker"),
]

# Kannada state names -> English (for context extraction from Kannada input)
KANNADA_STATE_MAP = {
    "ಕರ್ನಾಟಕ": "Karnataka", "ಕೇರಳ": "Kerala", "ಮಹಾರಾಷ್ಟ್ರ": "Maharashtra",
    "ತಮಿಳುನಾಡು": "Tamil Nadu", "ಬಿಹಾರ": "Bihar", "ರಾಜಸ್ಥಾನ": "Rajasthan",
    "ಆಂಧ್ರ ಪ್ರದೇಶ": "Andhra Pradesh", "ತೆಲಂಗಾಣ": "Telangana",
    "ಗುಜರಾತ್": "Gujarat", "ಪಂಜಾಬ್": "Punjab", "ಮಧ್ಯ ಪ್ರದೇಶ": "Madhya Pradesh",
    "ಉತ್ತರ ಪ್ರದೇಶ": "Uttar Pradesh", "ಪಶ್ಚಿಮ ಬಂಗಾಳ": "West Bengal",
    "ಒಡಿಶಾ": "Odisha", "ದೆಹಲಿ": "Delhi", "ಹರ್ಯಾಣ": "Haryana",
}

# Bengali state names/variants -> English (for context extraction from Bengali input)
BENGALI_STATE_MAP = {
    "পশ্চিমবঙ্গ": "West Bengal", "পশ্চিম বঙ্গ": "West Bengal",
    "বিহার": "Bihar", "কর্ণাটক": "Karnataka", "কেরল": "Kerala",
    "মহারাষ্ট্র": "Maharashtra", "তামিলনাড়ু": "Tamil Nadu", "রাজস্থান": "Rajasthan",
    "আন্ধ্রপ্রদেশ": "Andhra Pradesh", "তেলেঙ্গানা": "Telangana",
    "গুজরাত": "Gujarat", "পাঞ্জাব": "Punjab", "মধ্যপ্রদেশ": "Madhya Pradesh",
    "উত্তরপ্রদেশ": "Uttar Pradesh", "ওড়িশা": "Odisha", "দিল্লি": "Delhi",
    "হরিয়ানা": "Haryana", "ত্রিপুরা": "Tripura", "অসম": "Assam",
}

# Bengali occupation patterns (regex on original text)
BENGALI_OCCUPATION_PATTERNS = [
    (r"কৃষক|কৃষিকাজ|চাষ", "farmer"),
    (r"ছাত্র|ছাত্রী|পড়াশোনা", "student"),
    (r"বয়স্ক|বৃদ্ধ|পেনশনভোগী", "senior citizen"),
    (r"ব্যবসায়ী|উদ্যোক্তা|ব্যবসা", "entrepreneur"),
    (r"শ্রমিক|কর্মচারী|কাজ", "worker"),
    (r"মহিলা|স্ত্রী|গৃহবধূ", "homemaker"),
]

# Tamil state names/variants -> English (for context extraction from Tamil input)
TAMIL_STATE_MAP = {
    "தமிழ்நாடு": "Tamil Nadu", "தமிழ்நாட்டில்": "Tamil Nadu", "தமிழ்நாட்டு": "Tamil Nadu",
    "கருநாடகம்": "Karnataka", "கேரளம்": "Kerala",
    "மகாராஷ்டிரம்": "Maharashtra", "பீகார்": "Bihar", "ராஜஸ்தான்": "Rajasthan",
    "ஆந்திரா": "Andhra Pradesh", "தெலுங்கானா": "Telangana",
    "குஜராத்": "Gujarat", "பஞ்சாப்": "Punjab", "மத்தியப் பிரதேசம்": "Madhya Pradesh",
    "உத்தரப் பிரதேசம்": "Uttar Pradesh", "மேற்கு வங்கம்": "West Bengal",
    "ஒடிசா": "Odisha", "டெல்லி": "Delhi", "ஹரியானா": "Haryana",
}

# Tamil occupation patterns (regex on original text)
TAMIL_OCCUPATION_PATTERNS = [
    (r"விவசாயி|விவசாயிகள்|விவசாயம்", "farmer"),
    (r"மாணவர்|மாணவி|படிப்பு", "student"),
    (r"முதியோர்|வயதானவர்|மூப்பான", "senior citizen"),
    (r"வணிகர்|தொழிலதிபர்|வியாபாரம்", "entrepreneur"),
    (r"தொழிலாளர்|ஊழியர்|வேலை", "worker"),
    (r"மகளிர்|பெண்|பெண்கள்", "homemaker"),
]

# Kannada occupation patterns (regex on original text; Kannada has no case)
KANNADA_OCCUPATION_PATTERNS = [
    (r"ರೈತ|ರೈತರು|ಕೃಷಿ", "farmer"),
    (r"ವಿದ್ಯಾರ್ಥಿ|ವಿದ್ಯಾರ್ಥಿನಿ|ಅಧ್ಯಯನ", "student"),
    (r"ಹಿರಿಯ|ವೃದ್ಧ|ಹಿರಿಯ ನಾಗರಿಕ|ಪಿಂಚಣಿದಾರ", "senior citizen"),
    (r"ವ್ಯಾಪಾರಿ|ಉದ್ಯಮಿ|ವ್ಯಾಪಾರ", "entrepreneur"),
    (r"ಕಾರ್ಮಿಕ|ಉದ್ಯೋಗಿ|ಕೆಲಸ", "worker"),
    (r"ಮಹಿಳೆ|ಸ್ತ್ರೀ|ಹೆಂಗಸು", "homemaker"),  # often used for women schemes
]

CATEGORIES = {
    r"\bsc\s*/\s*st\b|\bsc\s+st\b|\bsc\s*&\s*st\b|\bsc\s+and\s+st\b": "SC/ST",
    r"\bsc\b|\bschedul\w+\s*caste\b|\bdalit\b": "SC",
    r"\bst\b|\bschedul\w+\s*tribe\b|\btribal\b|\badivasi\b": "ST",
    r"\bobc\b|\bother\s*backward\b": "OBC",
    r"\bgeneral\s*category\b|\bunreserved\b": "General",
    r"\bminority\b|\bmuslim\b|\bchristian\b|\bsikh\b|\bbuddhist\b|\bjain\b|\bparsi\b": "Minority",
}

# Education level: granular extraction for filtering (undergrad vs postgrad vs PhD)
# Order matters: check most specific first (phd → postgraduate → undergraduate → diploma → 12th → 10th)
EDUCATION_LEVEL_PATTERNS = [
    # PhD / doctorate
    (r"\bph\.?d\b|\bdoctorate\b|\bdoctoral\b|\bresearch\s+scholar\b|\bresearch\s+student\b", "phd"),
    # Postgraduate / masters
    (r"\bm\.?sc\b|\bm\.?tech\b|\bmtech\b|\bmba\b|\bm\.?b\.?a\b|\bm\.?e\.?\b|\bme\s+student\b|\bmasters\b|\bmaster'?s\b|\bpost.?graduate\b|\bpost.?graduation\b|\bpg\s+student\b|\bp\.?g\.?\b|\bmphil\b|\bm\.?phil\b", "postgraduate"),
    # Undergraduate / degree
    (r"\bengineering\s+student\b|\bbe\s+student\b|\bbtech\b|\bb\.?tech\b|\bb\.?e\b|\bgraduation\b|\bdegree\s+student\b|\bundergraduate\b|\bunder.?graduate\b|\bug\s+student\b|\bb\.?a\.?\b|\bb\.?sc\b|\bb\.?com\b|\bbba\b|\bb\.?b\.?a\b|\bmbbs\b|\bbds\b|\bcollege\s+student\b|\buniversity\s+student\b", "undergraduate"),
    # Diploma
    (r"\bdiploma\s+student\b|\bdiploma\b", "diploma"),
    # 12th / higher secondary
    (r"\b12th\b|\b12\s+th\b|\bclass\s*12\b|\bhigher\s+secondary\b|\bhsc\b|\bhsce\b|\bpuc\b|\bintermediate\b|\bplus\s*two\b", "12th"),
    # 10th / matriculation
    (r"\b10th\b|\b10\s+th\b|\bclass\s*10\b|\bssc\b|\bmatriculation\b|\bmatric\b|\bschool\s+student\b", "10th"),
]
# Fallback: "higher" = post-matric, "school" = pre-matric (for backward compat)
EDUCATION_HIGHER_PATTERNS = [
    r"\bcollege\b", r"\buniversity\b", r"\bdegree\b", r"\bprofessional\s+course\b",
    r"\bmedical\s+student\b", r"\blaw\b", r"\bllb\b", r"\bnursing\b", r"\bpolytechnic\b",
    r"\bpost.?matric\b", r"\bclass\s*1[1-2]\b", r"\b1[1-2]th\b", r"\bhigher\s+secondary\b",
    r"\bhigher\s+education\b", r"\bug\b", r"\bpg\b", r"\bca\b", r"\bcs\b", r"\bicwa\b",
]
EDUCATION_SCHOOL_PATTERNS = [
    r"\bpre.?matric\b", r"\bclass\s*[1-9]\b(?!\d)", r"\bclass\s*10\b",
    r"\b[1-9]th\s+(?:class|standard|std)\b", r"\b10th\s+(?:class|standard|std)\b",
    r"\bprimary\s+school\b", r"\bmiddle\s+school\b", r"\bhigh\s+school\b",
]

# BPL / income status
BPL_PATTERNS = [
    r"\bbpl\b", r"\bbelow\s+poverty\b", r"\bpoor\b", r"\blow\s+income\b",
    r"\beconomically\s+weak\b", r"\bews\b", r"\bgarib\b",
    r"\bration\s+card\b.*\b(?:yellow|pink|priority)\b",
]

# Disability
DISABILITY_PATTERNS = [
    r"\bdisabl\w+\b", r"\bpwd\b", r"\bperson\s+with\s+disabilit\w+\b",
    r"\bhandicap\w*\b", r"\bdivyang\b", r"\bblind\b", r"\bdeaf\b",
    r"\borthopedic\w*\b", r"\bcerebral\s+palsy\b", r"\bmental\s+retard\w*\b",
    r"\bintellectual\s+disabilit\w*\b",
]

# Residence
RESIDENCE_PATTERNS = {
    r"\brural\b|\bvillage\b|\bgram\b|\bpanchayat\b": "rural",
    r"\burban\b|\bcity\b|\btown\b|\bmetro\b|\bmunicipal\b|\bnagar\b": "urban",
}

# Marital / family
MARITAL_PATTERNS = {
    r"\bwidow\b|\bvidhwa\b": "widow",
    r"\bsingle\s+mother\b|\bsingle\s+parent\b": "single parent",
    r"\bpregnant\b|\bmaternity\b|\bgarbhvati\b|\bexpecting\b": "pregnant",
    r"\borphan\b|\banath\b": "orphan",
}

# Specific need / type of help detection (English + Hindi)
NEED_PATTERNS = {
    # Education (incl. Hindi: छात्रवृत्ति, शिक्षा, etc.)
    r"\bscholarship\b|\bscholarships\b|\bfellowship\b|\bstipend\b|\bfreeship\b|\bfee\s+waiver\b|\btuition\b|\bछात्रवृत्ति\b": "scholarship",
    # Loans
    r"\bloan\b|\bloans\b|\bmudra\b|\bcredit\b|\bfinance\b|\bfunding\b|\bborrowing\b": "loan",
    # Pension / old age
    r"\bpension\b|\bretirement\b|\bold\s*age\b|\bvridh\b": "pension",
    # Agriculture / farming (BEFORE health so "crop insurance" matches agriculture, not health)
    r"\bcrop\b|\bfarming\b|\bseed\b|\birrigation\b|\bfertilizer\b|\bkhet\b|\bfasal\b|\bharvest\b|\bcrop\s+insurance\b": "agriculture_support",
    # Health / medical
    r"\bhealth\s*insurance\b|\bhealth\s*cover\b|\bhospital\b|\bayushman\b|\btreatment\b|\bmedical\b|\bsurgery\b|\bdisease\b|\bhealth\b": "health_insurance",
    # Housing
    r"\bhousing\b|\bawas\b|\bhouse\b|\bshelter\b|\bpmay\b|\bflat\b|\brent\b": "housing",
    # Maternity / pregnancy
    r"\bmaternity\b|\bpregnant\b|\bchild\s*birth\b|\bdelivery\b|\bgarbhvati\b": "maternity",
    # Skill / training
    r"\bskill\b|\btraining\b|\bvocational\b|\bapprentice\b|\binternship\b|\bcertification\b|\bcourse\b": "skill_training",
    # Employment / job
    r"\bjob\b|\bemployment\b|\bnaukri\b|\brozgar\b|\bwork\b|\bplacement\b": "employment",
    # Business / entrepreneurship
    r"\bbusiness\b|\bentrepreneur\b|\bstartup\b|\bstart-?up\b|\budyam\b|\bmsme\b|\bself[- ]?employ\b": "business_support",
    # Marriage / wedding
    r"\bmarriage\b|\bwedding\b|\bshadi\b|\bvivah\b|\bdowry\b|\bkanyadan\b|\bkanya\b": "marriage",
    # Financial help / money / cash
    r"\bmoney\b|\bcash\b|\bfinancial\s+help\b|\bfinancial\s+assist\b|\bpaisa\b|\barthik\b|\bdirect\s+benefit\b|\bDBT\b": "financial_assistance",
    # Subsidy / grant
    r"\bsubsidy\b|\bgrant\b|\brebate\b|\bconcession\b": "subsidy",
    # Legal / protection
    r"\blegal\b|\bprotection\b|\bviolence\b|\babuse\b|\bsafety\b": "legal_protection",
    # Food / nutrition
    r"\bfood\b|\bration\b|\bnutrition\b|\bmeal\b|\bmid[- ]?day\b|\bannapurna\b": "food_nutrition",
    # Disability
    r"\bdisability\b|\bdivyang\b|\bhandicap\b|\bblind\b|\bdeaf\b|\bPWD\b": "disability_support",
    # Generic insurance (catch-all for "insurance" not matched above)
    r"\binsurance\b": "health_insurance",
}

# Required context fields before recommending
# Minimum: occupation, state, age. Preferred: help_type, caste, gender, income.
CONTEXT_FIELDS = ["occupation", "state", "age", "help_type", "gender", "caste_category"]
MIN_CONTEXT_FOR_RECOMMENDATION = 3  # occupation + state + age


def extract_context_from_text(text: str) -> Dict[str, str]:
    """Extract every possible user attribute from a single message."""
    ctx: Dict[str, str] = {}
    t = text.lower()

    # --- State (English + Gujarati + Marathi + Bengali + Tamil + Kannada) ---
    for gujarati_name, eng_state in GUJARATI_STATE_MAP.items():
        if gujarati_name in text:
            ctx["state"] = eng_state
            break
    if "state" not in ctx:
        for marathi_name, eng_state in MARATHI_STATE_MAP.items():
            if marathi_name in text:
                ctx["state"] = eng_state
                break
    if "state" not in ctx:
        for bengali_name, eng_state in BENGALI_STATE_MAP.items():
            if bengali_name in text or (bengali_name + "থেকে") in text or (bengali_name + "এর") in text:
                ctx["state"] = eng_state
                break
    if "state" not in ctx:
        for tamil_name, eng_state in TAMIL_STATE_MAP.items():
            if tamil_name in text or (tamil_name + "இலிருந்து") in text or (tamil_name + "வில்") in text:
                ctx["state"] = eng_state
                break
    if "state" not in ctx:
        for kannada_name, eng_state in KANNADA_STATE_MAP.items():
            if kannada_name in text or (kannada_name + "ದಿಂದ") in text or (kannada_name + "ದ") in text:
                ctx["state"] = eng_state
                break
    if "state" not in ctx:
        for state in sorted(INDIAN_STATES, key=len, reverse=True):
            if state in t:
                ctx["state"] = STATE_DISPLAY.get(state, state.title())
                break
    if "state" not in ctx:
        for city, state_name in CITY_TO_STATE.items():
            if city in t:
                ctx["state"] = state_name
                break

    # --- Occupation (English + Gujarati + Marathi + Bengali + Tamil + Kannada) ---
    for pattern, occ in GUJARATI_OCCUPATION_PATTERNS:
        if re.search(pattern, text):
            ctx["occupation"] = occ
            break
    if "occupation" not in ctx:
        for pattern, occ in MARATHI_OCCUPATION_PATTERNS:
            if re.search(pattern, text):
                ctx["occupation"] = occ
                break
    if "occupation" not in ctx:
        for pattern, occ in BENGALI_OCCUPATION_PATTERNS:
            if re.search(pattern, text):
                ctx["occupation"] = occ
                break
    if "occupation" not in ctx:
        for pattern, occ in TAMIL_OCCUPATION_PATTERNS:
            if re.search(pattern, text):
                ctx["occupation"] = occ
                break
    if "occupation" not in ctx:
        for pattern, occ in KANNADA_OCCUPATION_PATTERNS:
            if re.search(pattern, text):
                ctx["occupation"] = occ
                break
    if "occupation" not in ctx:
        for pattern, occ in OCCUPATIONS.items():
            if re.search(pattern, t, re.I):
                ctx["occupation"] = occ
                break

    # --- Gender ---
    for pattern, g in GENDERS.items():
        if re.search(pattern, t, re.I):
            ctx["gender"] = g
            break

    # --- Caste / category ---
    for pattern, cat in CATEGORIES.items():
        if re.search(pattern, t, re.I):
            ctx["caste_category"] = cat
            break

    # --- Age ---
    for pat in [
        r"\b(\d{1,2})\s*(?:years?|yrs?|year)?\s*old\b",
        r"\bage\s*(?:is\s*)?(\d{1,2})\b",
        r"\bi(?:'?m| am)\s*(\d{1,2})\b",
        r"\b(\d{1,2})\s*sal\s*(?:ka|ki|ke|kaa)?\b",  # Hindi: 35 sal ka
        r"\b(?:umr|umar)\s*(?:hai\s*)?(\d{1,2})\b",  # Hindi: umr 35
        r"(?:ವಯಸ್ಸು|ವಯಸು)\s*(\d{1,2})\b",  # Kannada: ವಯಸ್ಸು 35
        r"ನನ್ನ\s*(?:ವಯಸ್ಸು|ವಯಸು)\s*(\d{1,2})\b",  # Kannada: ನನ್ನ ವಯಸ್ಸು 35
        r"(?:வயது)\s*(\d{1,2})\b",  # Tamil: வயது 35
        r"என்\s*வயது\s*(\d{1,2})\b",  # Tamil: என் வயது 35
        r"বয়স\s*(\d{1,2})\b",  # Bengali: বয়স 35
        r"আমার\s*বয়স\s*(\d{1,2})\b",  # Bengali: আমার বয়স 35
        r"वय\s*(\d{1,2})\b",  # Marathi: वय 35
        r"माझे\s*वय\s*(\d{1,2})\b",  # Marathi: माझे वय 35
        r"ઉંમર\s*(\d{1,2})\b",  # Gujarati: ઉંમર 35
        r"મારી\s*ઉંમર\s*(\d{1,2})\b",  # Gujarati: મારી ઉંમર 35
    ]:
        m = re.search(pat, t, re.I)
        if m:
            age = int(m.group(1))
            if 5 <= age <= 100:
                ctx["age"] = str(age)
            break

    # --- Income / income_level ---
    m = re.search(
        r"(?:income|earn|salary|annual\s+income).{0,25}?([\d,.]+)\s*(?:lakh|lac|lpa|per\s*(?:annum|year|month)|/\s*(?:year|month|annum))",
        t, re.I,
    )
    if not m:
        # Match "1.5 lakh annual income" (number before "lakh")
        m = re.search(
            r"([\d,.]+)\s*(?:lakh|lac|lpa)\s*(?:annual\s+)?(?:income|per\s*(?:annum|year))?",
            t, re.I,
        )
        if m:
            val = m.group(0).strip()
            # Normalize to "X lakh" format for consistency
            num = m.group(1).replace(",", "")
            if "lakh" in t[m.start() : m.end() + 20].lower() or "lac" in t[m.start() : m.end() + 20].lower() or "lpa" in t[m.start() : m.end() + 20].lower():
                ctx["income"] = f"{num} lakh"
            else:
                ctx["income"] = val
            ctx["income_level"] = ctx["income"]
    if m and "income_level" not in ctx:
        ctx["income"] = m.group(0).strip()
        ctx["income_level"] = ctx["income"]

    # --- Education level (granular: phd, postgraduate, undergraduate, diploma, 12th, 10th) ---
    for pat, level in EDUCATION_LEVEL_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["education_level"] = level
            break
    if "education_level" not in ctx:
        for pat in EDUCATION_HIGHER_PATTERNS:
            if re.search(pat, t, re.I):
                ctx["education_level"] = "higher"  # fallback: post-matric
                break
    if "education_level" not in ctx:
        for pat in EDUCATION_SCHOOL_PATTERNS:
            if re.search(pat, t, re.I):
                ctx["education_level"] = "school"  # fallback: pre-matric
                break

    # --- BPL / EWS ---
    for pat in BPL_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["bpl"] = "yes"
            ctx["income_level"] = ctx.get("income_level") or "bpl"
            break

    # --- Disability ---
    for pat in DISABILITY_PATTERNS:
        if re.search(pat, t, re.I):
            ctx["disability"] = "yes"
            break

    # --- Rural / Urban ---
    for pat, val in RESIDENCE_PATTERNS.items():
        if re.search(pat, t, re.I):
            ctx["residence"] = val
            break

    # --- Marital / special family status ---
    for pat, val in MARITAL_PATTERNS.items():
        if re.search(pat, t, re.I):
            ctx["family_status"] = val
            break

    # --- Specific need / type of help ---
    for pat, need in NEED_PATTERNS.items():
        if re.search(pat, t, re.I):
            ctx["specific_need"] = need
            ctx["help_type"] = need  # Also track as help_type for question flow
            break

    # --- Negations ---
    for pattern, cat in CATEGORIES.items():
        neg = re.search(r"(?:not|no|neither|don'?t|isn'?t|i'?m not)\s+(?:a\s+)?" + pattern, t, re.I)
        if neg and ctx.get("caste_category") == cat:
            del ctx["caste_category"]

    neg_dis = re.search(r"(?:not|no|don'?t have)\s+(?:a\s+)?(?:disabl|handicap|pwd|divyang)", t, re.I)
    if neg_dis and "disability" in ctx:
        del ctx["disability"]

    neg_bpl = re.search(r"(?:not|no)\s+(?:bpl|below poverty|ews|poor|economically weak)", t, re.I)
    if neg_bpl and "bpl" in ctx:
        del ctx["bpl"]

    return ctx


def build_cumulative_context(
    history: Optional[List[Any]],
    current_message: str,
) -> Dict[str, str]:
    """Walk entire conversation building user context. Later messages override."""
    ctx: Dict[str, str] = {}
    for msg in (history or []):
        role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
        content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
        if role == "user" and content:
            ctx.update(extract_context_from_text(content))
    ctx.update(extract_context_from_text(current_message))
    return ctx


def context_completeness(ctx: Dict[str, str]) -> int:
    return sum(1 for f in CONTEXT_FIELDS if ctx.get(f))


def missing_context_fields(ctx: Dict[str, str]) -> List[str]:
    return [f for f in CONTEXT_FIELDS if not ctx.get(f)]


def _is_valid(val: Optional[str]) -> bool:
    """Return True if a context value is present and meaningful."""
    if not val:
        return False
    return val.strip().lower() not in ("unknown", "any", "all india", "")


def _is_known(val: Optional[str]) -> bool:
    """Value is present and not a placeholder/unknown."""
    if not val:
        return False
    s = str(val).strip().lower()
    return s not in ("unknown", "any", "", "none", "not specified", "all india", "n/a")


def has_enough_context(user_context: Optional[Dict[str, str]]) -> bool:
    """
    ALL 6 fields must be known before RAG runs.
    """
    if not user_context:
        return False

    def is_known(val: Optional[str]) -> bool:
        return (
            val
            and str(val).strip().lower()
            not in ["unknown", "any", "", "none", "not specified", "n/a"]
        )

    required_fields = [
        "occupation",
        "state",
        "age",
        "caste_category",
        "income_level",
        "gender",
    ]

    def get_val(f: str) -> Optional[str]:
        v = user_context.get(f)
        if f == "income_level":
            v = v or user_context.get("income")
        return v

    missing_list = [f for f in required_fields if not is_known(get_val(f))]
    if missing_list:
        logger.info("Missing fields before RAG: %s", missing_list)
        return False

    logger.info("All 6 fields collected. Running RAG.")
    return True


def get_missing_fields(user_context: Optional[Dict[str, str]]) -> List[str]:
    """Returns list of field names (human-readable labels) that are still unknown."""
    if not user_context:
        return [
            "occupation",
            "state",
            "age",
            "caste category (SC/ST/OBC/General)",
            "annual income",
            "gender",
        ]

    def is_known(val: Optional[str]) -> bool:
        return (
            val
            and str(val).strip().lower()
            not in ["unknown", "any", "", "none", "not specified", "n/a"]
        )

    required = {
        "occupation": "occupation",
        "state": "state",
        "age": "age",
        "caste_category": "caste category (SC/ST/OBC/General)",
        "income_level": "annual income",
        "gender": "gender",
    }

    result = []
    for field, label in required.items():
        val = user_context.get(field)
        if field == "income_level":
            val = val or user_context.get("income")
        if not is_known(val):
            result.append(label)
    return result


def is_ready_to_recommend(user_context: Optional[Dict[str, str]]) -> bool:
    """
    Show schemes when we have minimum: occupation + state.
    RAG runs when these two are known.
    """
    return has_enough_context(user_context)


# ============================================================
# 2. MULTI-DIMENSIONAL SCHEME FILTER
#    Each filter returns True = keep, False = reject.
#    Runs every filter in sequence on each candidate.
# ============================================================

def _get_elig(scheme: dict) -> dict:
    """Safely extract eligibility_criteria dict."""
    elig = scheme.get("eligibility_criteria") or {}
    return elig if isinstance(elig, dict) else {}


def _scheme_text(scheme: dict) -> str:
    """Combine name + brief + eligibility text for keyword searching."""
    name = (scheme.get("scheme_name") or "")
    brief = (scheme.get("brief_description") or "")
    elig = _get_elig(scheme)
    raw = (elig.get("raw_eligibility_text") or "")
    return f"{name} {brief} {raw}".lower()


# --- Filter: State ---
def _filter_state(scheme: dict, user_state: str) -> bool:
    elig = _get_elig(scheme)
    scheme_state = (elig.get("state") or "").strip().lower()
    if not scheme_state or scheme_state in ("all india", "any", "all", "nationwide"):
        return True
    # "All India (..." or state contains user_state
    if "all india" in scheme_state:
        return True
    user_lower = user_state.strip().lower()
    return user_lower in scheme_state or scheme_state in user_lower


# --- Filter: Gender ---
def _filter_gender(scheme: dict, user_gender: str) -> bool:
    elig = _get_elig(scheme)
    sg = (elig.get("gender") or "any").strip().lower()
    if sg in ("any", ""):
        return True
    ug = user_gender.lower()
    # Exact match
    if sg == ug:
        return True
    # Use word boundary check to prevent "male" matching inside "female"
    if re.search(r"\b" + re.escape(ug) + r"\b", sg):
        return True
    return False


# --- Filter: Caste / Category ---
def _filter_caste(scheme: dict, user_caste: str) -> bool:
    elig = _get_elig(scheme)
    sc = (elig.get("caste_category") or "any").strip().lower()
    if sc in ("any", ""):
        return True
    uc = user_caste.lower()
    # "any (higher subsidy for SC/ST)" → keep
    if "any" in sc:
        return True
    # Exact or substring
    if uc in sc or sc in uc:
        return True
    # Handle SC/ST combined: user=SC → scheme SC/ST is OK
    if uc in ("sc", "st") and "sc/st" in sc:
        return True
    if uc == "sc/st" and ("sc" in sc or "st" in sc):
        return True
    # "general" user should NOT see SC/ST/OBC-only schemes
    if uc == "general" and re.search(r"\bsc\b|\bst\b|\bobc\b|\bminority\b", sc):
        return False
    return False


# --- Filter: Age ---
def _parse_age_range(age_str: str) -> Optional[Tuple[int, int]]:
    """Parse age strings like '18-40', '60+', '<10', '18+' etc."""
    s = age_str.strip().lower()
    if not s or s in ("any", "all", "no limit"):
        return None
    m = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"(\d+)\s*\+", s)
    if m:
        return (int(m.group(1)), 120)
    m = re.search(r"<\s*(\d+)", s)
    if m:
        return (0, int(m.group(1)))
    m = re.search(r">\s*(\d+)", s)
    if m:
        return (int(m.group(1)), 120)
    return None


def _filter_age(scheme: dict, user_age: int) -> bool:
    elig = _get_elig(scheme)
    age_str = (elig.get("age_range") or "any").strip()
    rng = _parse_age_range(age_str)
    if rng is None:
        return True
    lo, hi = rng
    return lo <= user_age <= hi


# --- Filter: Occupation ---
def _filter_occupation(scheme: dict, user_occupation: str) -> bool:
    elig = _get_elig(scheme)
    so = (elig.get("occupation") or "any").strip().lower()
    if so in ("any", ""):
        return True
    uo = user_occupation.lower()
    # Direct match
    if uo in so or so in uo:
        return True
    # Farmer schemes: reject if user is student/entrepreneur/worker
    if "farmer" in so and uo not in ("farmer",):
        return False
    # Student schemes: allow (most student schemes have occ=student or any)
    if "student" in so and uo != "student":
        return False
    # Entrepreneur schemes
    if "entrepreneur" in so and uo not in ("entrepreneur",):
        return False
    # Senior citizen
    if "senior" in so and uo != "senior citizen":
        return False
    return True


# --- Filter: Education level (pre-matric vs post-matric) ---
def _scheme_is_pre_matric(text: str) -> bool:
    if re.search(r"\bpre[- ]?matric\b", text):
        return True
    # Mentions class 1-10 but NOT class 11-12 / college / post-matric
    if re.search(r"\bclass(?:es)?\s+(?:[1-9]|10)\b", text):
        if not re.search(r"\bclass\s*1[1-2]\b|\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b", text):
            return True
    return False


def _scheme_is_post_matric(text: str) -> bool:
    return bool(re.search(
        r"\bpost[- ]?matric\b|\bcollege\b|\buniversity\b|\bdegree\b|\bgraduate\b"
        r"|\bprofessional\s+course\b|\bengineering\b|\bmbbs\b|\bdiploma\b",
        text,
    ))


def _filter_education(scheme: dict, user_edu: str) -> bool:
    """Pre-matric vs post-matric: higher/undergrad/postgrad/phd/diploma reject pre-matric; school/10th/12th reject post-matric."""
    text = _scheme_text(scheme)
    higher_levels = ("higher", "undergraduate", "postgraduate", "phd", "diploma")
    school_levels = ("school", "10th", "12th")
    if user_edu in higher_levels:
        return not _scheme_is_pre_matric(text)
    if user_edu in school_levels:
        return not _scheme_is_post_matric(text)
    return True


# Education level: undergrad vs postgrad/PhD filtering
POSTGRAD_ONLY_KEYWORDS = [
    "phd", "ph.d", "doctorate", "doctoral",
    "postgraduate", "post graduate", "post-graduate",
    "pg student", "p.g",
    "msc", "m.sc", "mtech", "m.tech", "mba", "m.b.a",
    "me ", "m.e.", "masters", "master's",
    "mphil", "m.phil",
    "research scholar", "research student",
    "fellowship for phd", "doctoral fellowship",
    "junior research fellow", "jrf",
    "senior research fellow", "srf",
]
UNDERGRAD_LEVEL_KEYWORDS = [
    "undergraduate", "under graduate", "under-graduate",
    "ug student", "u.g",
    "btech", "b.tech", "be ", "b.e.",
    "bsc", "b.sc", "ba ", "b.a.", "bcom", "b.com",
    "bba", "b.b.a", "mbbs", "bds",
    "graduation", "degree student",
    "college student", "university student",
]


def _filter_by_education_level(scheme: dict, user_education_level: Optional[str]) -> bool:
    """
    Reject scheme if user is undergraduate and scheme is clearly postgrad/PhD only.
    Keep general schemes and undergrad-friendly schemes for undergrads.
    """
    if not user_education_level:
        return True
    ue = str(user_education_level).strip().lower()
    if ue in ("unknown", "any", "", "higher", "school"):
        return True

    eligibility = scheme.get("eligibility_criteria") or {}
    if not isinstance(eligibility, dict):
        eligibility = {}
    scheme_name = (scheme.get("scheme_name") or "").lower()
    brief = (scheme.get("brief_description") or "").lower()
    scheme_edu = str(
        eligibility.get("education_level", "")
        or eligibility.get("educational_qualification", "")
        or eligibility.get("qualification", "")
        or "",
    ).lower()
    raw_elig = (eligibility.get("raw_eligibility_text") or "").lower()
    all_text = f"{scheme_name} {scheme_edu} {brief[:300]} {raw_elig[:500]}"

    is_postgrad_only = any(kw in all_text for kw in POSTGRAD_ONLY_KEYWORDS)
    is_undergrad_friendly = any(kw in all_text for kw in UNDERGRAD_LEVEL_KEYWORDS)
    has_no_level_restriction = not is_postgrad_only and not is_undergrad_friendly

    if ue == "undergraduate":
        if is_postgrad_only and not is_undergrad_friendly:
            return False
        return True
    if ue in ("postgraduate", "masters"):
        return True
    if ue == "phd":
        return True
    if ue in ("12th", "diploma"):
        degree_keywords = ["graduation", "degree", "btech", "bsc", "ba ", "b.e."]
        if is_undergrad_friendly and not has_no_level_restriction:
            if any(kw in all_text for kw in degree_keywords):
                return False
        return True
    if ue == "10th":
        if is_undergrad_friendly and not has_no_level_restriction:
            degree_keywords = ["graduation", "degree", "btech", "bsc", "ba ", "b.e."]
            if any(kw in all_text for kw in degree_keywords):
                return False
        return True
    return True


# --- Filter: Disability ---
def _filter_disability(scheme: dict, user_has_disability: bool) -> bool:
    """If scheme is *only* for disabled people and user is NOT disabled, reject."""
    text = _scheme_text(scheme)
    name = (scheme.get("scheme_name") or "").lower()
    # Schemes with "disability" or "divyang" or "PWD" in the name are disability-specific
    is_disability_scheme = bool(re.search(
        r"\bdisabilit\w+\b|\bdivyang\b|\bpwd\b|\bhandicap\w*\b|\bblind\b|\bdeaf\b",
        name,
    ))
    if is_disability_scheme and not user_has_disability:
        return False
    return True


# --- Filter: Widow / Orphan specific schemes ---
def _filter_family_status(scheme: dict, user_status: Optional[str]) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    # Widow-only schemes
    if re.search(r"\bwidow\b|\bvidhwa\b", name) and user_status != "widow":
        return False
    # Orphan-only schemes
    if re.search(r"\borphan\b|\banath\b", name) and user_status != "orphan":
        return False
    return True


# --- Filter: Farmer-specific land schemes for non-farmers ---
def _filter_farmer_schemes(scheme: dict, user_occupation: str) -> bool:
    """Don't show crop insurance / Kisan schemes to non-farmers."""
    if user_occupation == "farmer":
        return True
    name = (scheme.get("scheme_name") or "").lower()
    if re.search(r"\bkisan\b|\bcrop\b|\bfasal\b|\bkcc\b|\bmandi\b|\be-?nam\b|\bagriculture\b", name):
        return False
    return True


# --- Filter: Senior citizen schemes for young people ---
def _filter_senior_schemes(scheme: dict, user_age: Optional[int], user_occupation: str) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    is_senior_scheme = bool(re.search(r"\bold\s*age\b|\bsenior\s*citizen\b|\bvaya\b|\bvridh\b", name))
    if not is_senior_scheme:
        return True
    if user_occupation == "senior citizen":
        return True
    if user_age and user_age >= 55:
        return True
    return False


# --- Filter: Children-only schemes for adults ---
def _filter_child_schemes(scheme: dict, user_age: Optional[int]) -> bool:
    name = (scheme.get("scheme_name") or "").lower()
    brief = (scheme.get("brief_description") or "").lower()
    # Schemes clearly for children (Sukanya, Beti Bachao, child labor, etc.)
    is_child_scheme = bool(re.search(
        r"\bchild\s+labour\b|\bbalika\b|\bbeti\b|\bsukanya\b|\bgirl\s+child\b",
        name,
    ))
    if is_child_scheme and user_age and user_age > 25:
        # Sukanya Samriddhi can be opened by parents, so check brief
        if "parent" in brief or "guardian" in brief:
            return True
        return False
    return True


# --- Filter: Specific need (scholarship vs loan vs pension etc.) ---
NEED_TO_BENEFIT_TYPES = {
    "scholarship": {"scholarship", "fellowship", "stipend", "freeship"},
    "loan": {"loan", "credit", "subsidized loan", "subsidized credit"},
    "pension": {"pension", "pension / investment"},
    "health_insurance": {"health insurance", "insurance"},
    "housing": {"housing", "housing subsidy"},
    "maternity": {"maternity", "maternity benefit"},
    "subsidy": {"subsidy", "capital subsidy"},
}

NEED_TO_KEYWORDS = {
    "scholarship": [r"\bscholarship\b", r"\bfellowship\b", r"\bstipend\b", r"\bfreeship\b", r"\bfee\s+waiver\b", r"\btuition\b"],
    "loan": [r"\bloan\b", r"\bcredit\b", r"\bmudra\b"],
    "pension": [r"\bpension\b", r"\bretirement\b"],
    "health_insurance": [r"\bhealth\b.*\binsurance\b", r"\bayushman\b", r"\bhospital\b"],
    "housing": [r"\bhousing\b", r"\bawas\b", r"\bshelter\b"],
    "maternity": [r"\bmaternity\b", r"\bpregnant\b", r"\bjanani\b"],
    "skill_training": [r"\bskill\b", r"\btraining\b", r"\bvocational\b", r"\bapprentice\b"],
}


def _filter_by_need(scheme: dict, user_need: str) -> bool:
    """
    If user has a specific need (e.g. scholarship), filter out schemes
    that are clearly a different type (e.g. loans, pensions).
    """
    if not user_need:
        return True  # No filter if no specific need

    # Check benefit_type field
    benefits = scheme.get("benefits") or {}
    if isinstance(benefits, dict):
        benefit_type = (benefits.get("benefit_type") or "").strip().lower()
    else:
        benefit_type = ""

    # 1. If the scheme's benefit_type matches the user's need → keep
    matching_types = NEED_TO_BENEFIT_TYPES.get(user_need, set())
    if matching_types and benefit_type:
        if benefit_type in matching_types:
            return True
        # If benefit type is CLEARLY a different need, reject
        # e.g. user wants scholarship but scheme is "Subsidized Loan"
        other_needs = set()
        for need, types in NEED_TO_BENEFIT_TYPES.items():
            if need != user_need:
                other_needs.update(types)
        if benefit_type in other_needs:
            return False

    # 2. Check scheme text for keywords matching the need
    text = _scheme_text(scheme)
    name = (scheme.get("scheme_name") or "").lower()

    # If scheme name or text has keywords matching user's need → keep
    need_keywords = NEED_TO_KEYWORDS.get(user_need, [])
    if need_keywords:
        for kw in need_keywords:
            if re.search(kw, name, re.I) or re.search(kw, text, re.I):
                return True

    # 3. If benefit_type is empty/generic ("Direct Cash Transfer", etc.), keep (might be relevant)
    generic_types = {"direct cash transfer", "financial assistance", "technical assistance",
                     "market access", "protection / rehabilitation", ""}
    if benefit_type in generic_types:
        return True

    # 4. For specific needs, reject if no positive signal
    if matching_types:
        return False

    return True


def filter_schemes_for_user(
    candidates: List[Dict[str, Any]],
    user_ctx: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Run ALL filters. A scheme must pass every applicable filter to survive.
    Logs what was removed and why.
    """
    user_state = user_ctx.get("state")
    user_gender = user_ctx.get("gender")
    user_caste = user_ctx.get("caste_category")
    user_age_str = user_ctx.get("age")
    user_age = int(user_age_str) if user_age_str and user_age_str.isdigit() else None
    user_occupation = user_ctx.get("occupation", "")
    user_edu = user_ctx.get("education_level")
    user_disability = user_ctx.get("disability") == "yes"
    user_family = user_ctx.get("family_status")
    user_need = user_ctx.get("specific_need")

    filtered = []
    reasons: Dict[str, int] = {}

    for s in candidates:
        rejected = None

        if user_state and not _filter_state(s, user_state):
            rejected = "state"
        elif user_gender and not _filter_gender(s, user_gender):
            rejected = "gender"
        elif user_caste and not _filter_caste(s, user_caste):
            rejected = "caste"
        elif user_age is not None and not _filter_age(s, user_age):
            rejected = "age"
        elif user_occupation and not _filter_occupation(s, user_occupation):
            rejected = "occupation"
        elif user_edu and not _filter_education(s, user_edu):
            rejected = "education_level"
        elif not _filter_by_education_level(s, user_ctx.get("education_level")):
            rejected = "education_level_filter"
        elif not _filter_disability(s, user_disability):
            rejected = "disability"
        elif user_family is not None and not _filter_family_status(s, user_family):
            rejected = "family_status"
        elif user_occupation and not _filter_farmer_schemes(s, user_occupation):
            rejected = "farmer_specific"
        elif not _filter_senior_schemes(s, user_age, user_occupation):
            rejected = "senior_specific"
        elif user_age is not None and not _filter_child_schemes(s, user_age):
            rejected = "child_specific"
        elif user_need and not _filter_by_need(s, user_need):
            rejected = "need_mismatch"

        if rejected:
            reasons[rejected] = reasons.get(rejected, 0) + 1
        else:
            filtered.append(s)

    if reasons:
        logger.info(
            "Filter results: %d→%d kept. Removed: %s",
            len(candidates), len(filtered),
            ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())),
        )

    return filtered


# ============================================================
# 3. ENDPOINTS
# ============================================================


def _start_pipeline_daemon() -> None:
    """Start the 24h pipeline daemon in a background thread if scheduler.enabled."""
    import json
    import threading
    from pathlib import Path

    backend_root = Path(__file__).resolve().parent.parent
    config_path = backend_root / "pipeline" / "pipeline_config.json"
    if not config_path.exists():
        return
    try:
        with config_path.open(encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("scheduler", {}).get("enabled", False):
            return
    except Exception:
        return

    def run_daemon_thread():
        try:
            from pipeline.daemon import run_daemon
            run_daemon(config_path=config_path, dry_run=False)
        except Exception as e:
            logger.warning("Pipeline daemon error: %s", e)

    th = threading.Thread(target=run_daemon_thread, daemon=True)
    th.start()
    logger.info("Pipeline daemon started (24h auto-update)")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Scheme Saathi Backend...")
    logger.info("Gemini model: %s", settings.GEMINI_MODEL)

    # DISABLED: Auto-scraper disabled for now. Pipeline code is intact, just not auto-starting.
    # To manually trigger: POST /admin/run-pipeline (if available) or run pipeline daemon manually.
    # _start_pipeline_daemon()

    # Initialize database schema (creates tables on first run).
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)

    logger.info("Total schemes: %s", rag_service.get_total_schemes())
    logger.info("Ready to serve requests")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "Welcome to Scheme Saathi API",
        "docs_url": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        gemini_ok = gemini_service.check_health()
        rag_ok = rag_service.check_health()
        total = rag_service.get_total_schemes()
        return HealthResponse(
            status="healthy" if (gemini_ok and rag_ok and total) else "degraded",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            gemini_status="connected" if gemini_ok else "disconnected",
            vector_db_status="loaded" if rag_ok else "error",
            total_schemes=total,
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Health check error: {str(e)}")


@app.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(request: SubscribeRequest, background_tasks: BackgroundTasks):
    """Subscribe to scheme alerts. Welcome email sent in background for new subscribers."""
    try:
        if "@" not in request.email or "." not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email address")

        ctx = request.user_context or {}
        state = ctx.get("state", "")
        occupation = ctx.get("occupation", "")

        is_new = add_subscriber(
            email=request.email,
            name=request.name or "",
            state=state,
            occupation=occupation,
            language=request.language,
            user_context=ctx,
        )

        if is_new:
            subscriber = {
                "email": request.email,
                "name": request.name or "there",
                "state": state,
                "occupation": occupation,
                "language": request.language,
            }
            background_tasks.add_task(send_welcome_email, subscriber)

        return SubscribeResponse(
            success=True,
            message="Successfully subscribed!" if is_new else "You're already subscribed.",
            is_new_subscriber=is_new,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Subscribe error: %s", e)
        raise HTTPException(status_code=500, detail="Subscription failed")


@app.post("/unsubscribe")
async def unsubscribe_user(request: UnsubscribeRequest):
    """Unsubscribe from scheme alerts."""
    try:
        unsubscribe_subscriber(request.email)
        return {"success": True, "message": "Unsubscribed successfully"}
    except Exception as e:
        logger.exception("Unsubscribe error: %s", e)
        raise HTTPException(status_code=500, detail="Unsubscribe failed")


@app.post("/admin/send-alerts")
async def trigger_alerts(background_tasks: BackgroundTasks):
    """Manually trigger scheme alerts to all subscribers. For demo: call after adding new schemes."""
    try:
        from datetime import timedelta

        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_schemes = [
            s
            for s in rag_service.schemes
            if (s.get("scraped_at") or s.get("last_updated") or "") >= week_ago
        ]
        if not new_schemes:
            import random

            new_schemes = random.sample(
                rag_service.schemes, min(5, len(rag_service.schemes))
            )

        background_tasks.add_task(send_alerts_to_matching_subscribers, new_schemes)
        return {
            "success": True,
            "message": f"Sending alerts for {len(new_schemes)} schemes",
            "schemes_count": len(new_schemes),
        }
    except Exception as e:
        logger.exception("Alert trigger error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/subscribers")
async def get_subscribers():
    """List all active subscribers (for demo)."""
    try:
        subs = get_all_active_subscribers()
        return {
            "total": len(subs),
            "subscribers": [
                {
                    "email": s["email"],
                    "name": s["name"],
                    "state": s["state"],
                    "occupation": s["occupation"],
                    "subscribed_at": s["subscribed_at"],
                }
                for s in subs
            ],
        }
    except Exception as e:
        logger.exception("Get subscribers error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Depends(get_current_user_id),
):
    """
    Main chat: extract context → decide gather/recommend → filter → respond.
    """
    query = (request.message or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info("Chat request: %s", query[:100])

    try:
        # 1. Extract context from FULL conversation (history + current message)
        full_conversation = list(request.conversation_history or []) + [
            ChatMessage(role="user", content=request.message)
        ]
        try:
            extracted_ctx = gemini_service.extract_user_context(full_conversation)
        except Exception as extract_err:
            logger.warning("Context extraction (LLM) failed, using regex fallback: %s", extract_err)
            extracted_ctx = {}
        if not extracted_ctx:
            extracted_ctx = build_cumulative_context(request.conversation_history, query)

        existing = request.user_context or {}
        all_keys = [
            "occupation", "state", "age", "gender",
            "caste_category", "income_level",
            "land_ownership", "education_level",
        ]

        def _is_valid(v):
            return v and str(v).strip().lower() not in [
                "unknown", "any", "", "none", "not specified", "n/a"
            ]

        merged_ctx: Dict[str, str] = {}
        for key in all_keys:
            extracted_val = extracted_ctx.get(key, "")
            existing_val = existing.get(key, "")
            if key == "income_level" and not extracted_val:
                extracted_val = extracted_ctx.get("income", "")
            if key == "income_level" and not existing_val:
                existing_val = existing.get("income", "")
            if _is_valid(extracted_val):
                merged_ctx[key] = str(extracted_val)
            elif _is_valid(existing_val):
                merged_ctx[key] = str(existing_val)
        if merged_ctx.get("income_level") and "income" not in merged_ctx:
            merged_ctx["income"] = merged_ctx["income_level"]
        user_ctx = merged_ctx

        missing = get_missing_fields(user_ctx)

        logger.info("DEBUG 2 - user_ctx: %s", user_ctx)
        logger.info("DEBUG 3 - is_ready: %s", is_ready_to_recommend(user_ctx))
        logger.info(
            "Context: %s | missing=%s",
            user_ctx, missing,
        )

        # 2. Run RAG only when we have minimum context (occupation + state)
        ready = is_ready_to_recommend(user_ctx)
        candidates: List[Dict[str, Any]] = []

        if ready:
            try:
                search_parts = [query]
                for key in ("occupation", "state", "gender", "caste_category", "education_level"):
                    val = user_ctx.get(key)
                    if val and str(val).lower() not in ("unknown", "any", ""):
                        search_parts.append(str(val))
                if user_ctx.get("specific_need"):
                    search_parts.append(str(user_ctx["specific_need"]))
                if user_ctx.get("disability") == "yes":
                    search_parts.append("disability divyang PWD")
                if user_ctx.get("bpl") == "yes":
                    search_parts.append("BPL below poverty economically weaker")
                if request.conversation_history:
                    for m in request.conversation_history[-4:]:
                        role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
                        content = getattr(m, "content", None) or (m.get("content", "") if isinstance(m, dict) else "")
                        if role == "user" and content:
                            search_parts.append(str(content))
                search_query = " ".join(search_parts)
                raw = rag_service.search_schemes(
                    query=search_query,
                    user_context=user_ctx,
                    top_k=50,
                )
                logger.info("DEBUG 4 - RAG results count: %s", len(raw))
                candidates = filter_schemes_for_user(raw or [], user_ctx)
                candidates = (candidates or [])[:20]
                logger.info("DEBUG 5 - After filtering: %s", len(candidates))
                logger.info("RAG returned %d candidates (ready=True)", len(candidates))
            except Exception as rag_err:
                logger.exception("RAG or filter failed (returning no schemes): %s", rag_err)
                candidates = []

        else:
            logger.info("Skipping RAG — need occupation + state (ready=False)")

        candidates = candidates or []
        for s in candidates:
            s["source_url"] = s.get("source_url") or ""
            s["official_website"] = s.get("official_website") or ""
        logger.info("DEBUG 6 - Final schemes count: %s", len(candidates))
        logger.info("DEBUG 7 - needs_more_info: %s", not ready)
        logger.info("Returning %d schemes", len(candidates))

        try:
            reply = gemini_service.chat(
                user_message=query,
                conversation_history=request.conversation_history,
                matched_schemes=candidates if ready else None,
                user_context=user_ctx,
                missing_fields=missing,
                language=request.language,
            )
        except Exception as llm_err:
            logger.exception("LLM chat failed: %s", llm_err)
            reply = (
                "I found some schemes for you below, but I couldn't generate a full response right now. "
                "Please try again in a moment."
            )
        if not reply or not str(reply).strip():
            reply = "Here are some schemes that might be relevant for you."

        persistent_chat_id: int | None = None

        # 4. Persist conversation to DB when user is authenticated
        # (Supabase JWT present). WhatsApp / anonymous calls skip this.
        if user_id is not None:
            logger.info("Authenticated user_id=%s; persisting chat to DB.", user_id)
            try:
                chat_obj, _history = await get_or_create_chat_for_message(
                    db,
                    user_id=user_id,
                    chat_id=request.chat_id,
                )
                if chat_obj:
                    persistent_chat_id = chat_obj.id
                    await append_message(db, chat_obj.id, user_id, "user", query)
                    await append_message(db, chat_obj.id, user_id, "assistant", reply)
                    logger.info("Saved chat_id=%s with 2 messages for user_id=%s", chat_obj.id, user_id)
                else:
                    logger.warning("get_or_create_chat_for_message returned None for user_id=%s", user_id)
            except Exception as db_err:
                logger.exception("Failed to persist chat to DB: %s", db_err)
                # Don't fail the request; the AI reply was already generated.
        else:
            logger.debug("Anonymous request; skipping DB persistence.")

        # Ensure schemes is always a list with at least scheme_id/scheme_name for frontend
        final_schemes: List[Dict[str, Any]] = []
        for s in (candidates or []):
            if not isinstance(s, dict):
                continue
            final_schemes.append({
                **s,
                "scheme_id": s.get("scheme_id") or s.get("id") or "",
                "scheme_name": s.get("scheme_name") or s.get("name") or s.get("title") or "Scheme",
                "source_url": s.get("source_url") or "",
                "official_website": s.get("official_website") or "",
            })
        logger.info("RETURNING schemes count: %s", len(final_schemes))
        logger.info(
            "RETURNING first scheme: %s",
            final_schemes[0].get("scheme_name") if final_schemes else "NONE",
        )
        return ChatResponse(
            message=reply,
            chat_id=persistent_chat_id,
            schemes=final_schemes,
            needs_more_info=not ready,
            extracted_context=user_ctx if user_ctx else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/schemes")
async def list_schemes(
    category: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 20,
):
    try:
        schemes: List[Dict[str, Any]] = list(rag_service.schemes)
        if category:
            cat_lower = category.strip().lower()
            schemes = [s for s in schemes if (s.get("category") or "").lower() == cat_lower]
        if state:
            schemes = [s for s in schemes if _filter_state(s, state)]
        return {"total": len(schemes[:limit]), "schemes": schemes[:limit]}
    except Exception as e:
        logger.exception("List schemes failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schemes/categories")
async def list_categories():
    return {"categories": rag_service.get_categories()}


@app.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    try:
        scheme = rag_service.get_scheme_by_id(scheme_id)
        if scheme is None:
            raise HTTPException(status_code=404, detail="Scheme not found")
        return scheme
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get scheme failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SchemeSearchResponse)
async def search_schemes(request: SchemeSearchRequest):
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    user_ctx: Dict[str, Any] = {}
    if request.state:
        user_ctx["state"] = request.state
    if request.category:
        user_ctx["category"] = request.category

    results = rag_service.search_schemes(
        query=query,
        user_context=user_ctx if user_ctx else None,
        top_k=request.top_k or settings.TOP_K_SCHEMES,
    )
    results = filter_schemes_for_user(results, user_ctx)

    return SchemeSearchResponse(
        query=query,
        total_matches=len(results),
        schemes=results,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
