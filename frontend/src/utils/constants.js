export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const APP_NAME = 'Scheme Saathi'
export const APP_TAGLINE = 'Your AI Guide to Government Schemes'
export const APP_DESCRIPTION = "Discover government schemes you're eligible for through AI-powered conversations. Simple, fast, and free."

export const FEATURES = [
  {
    title: 'AI-Powered Discovery',
    description: 'Natural conversations to find schemes that match your exact situation',
    icon: 'brain',
  },
  {
    title: '850+ Schemes',
    description: 'Comprehensive database covering agriculture, education, healthcare, and more',
    icon: 'database',
  },
  {
    title: 'Instant Eligibility',
    description: 'Know if you qualify before applying, saving time and effort',
    icon: 'check',
  },
  {
    title: 'Multi-Language',
    description: 'Access in English and Hindi, with more languages coming soon',
    icon: 'globe',
  },
]

export const HOW_IT_WORKS = [
  {
    step: 1,
    title: 'Start a Conversation',
    description: 'Tell us about yourself - your occupation, state, and needs',
  },
  {
    step: 2,
    title: 'Get Matched Schemes',
    description: 'Our AI finds relevant schemes based on your eligibility',
  },
  {
    step: 3,
    title: 'Apply with Confidence',
    description: 'Get clear guidance on documents, process, and deadlines',
  },
]

export const STATISTICS = [
  { value: '850+', label: 'Government Schemes' },
  { value: '₹20L Cr', label: 'Annual Budget Available' },
  { value: '68%', label: 'Citizens Unaware' },
  { value: '100%', label: 'Free to Use' },
]

export const STORAGE_KEYS = {
  CHATS: 'scheme_saathi_chats',
  CURRENT_CHAT_ID: 'scheme_saathi_current_chat',
  USER_PREFERENCES: 'scheme_saathi_preferences',
  AUTH_TOKEN: 'scheme_saathi_auth_token',
  AUTH_USER: 'scheme_saathi_auth_user',
}

export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
}

export const SUGGESTIONS = {
  en: [
    { icon: "🌾", text: "I'm a farmer in Bihar with 2 acres of land" },
    { icon: "👩‍🎓", text: "I'm a student looking for scholarships" },
    { icon: "👴", text: "Senior citizen looking for welfare schemes" },
    { icon: "💼", text: "I want to start a small business" },
    { icon: "🏥", text: "Looking for health and medical schemes" },
    { icon: "👩", text: "Women empowerment schemes" },
  ],
  hi: [
    { icon: "🌾", text: "मैं बिहार का किसान हूं, 2 एकड़ जमीन है" },
    { icon: "👩‍🎓", text: "मुझे छात्रवृत्ति के लिए योजना चाहिए" },
    { icon: "👴", text: "बुजुर्ग हूं, सरकारी मदद चाहिए" },
    { icon: "💼", text: "छोटा व्यापार शुरू करना है, ऋण चाहिए" },
    { icon: "🏥", text: "स्वास्थ्य योजनाएं खोजनी हैं" },
    { icon: "👩", text: "महिलाओं के लिए सरकारी योजनाएं" },
  ],
  kn: [
    { icon: "🌾", text: "ನಾನು ಕರ್ನಾಟಕದ ರೈತ, 2 ಎಕರೆ ಜಮೀನು ಇದೆ" },
    { icon: "👩‍🎓", text: "ವಿದ್ಯಾರ್ಥಿ ವೇತನಕ್ಕಾಗಿ ಯೋಜನೆ ಬೇಕು" },
    { icon: "👴", text: "ಹಿರಿಯ ನಾಗರಿಕ, ಸರ್ಕಾರಿ ಸಹಾಯ ಬೇಕು" },
    { icon: "💼", text: "ಸಣ್ಣ ವ್ಯಾಪಾರ ಪ್ರಾರಂಭಿಸಲು loan ಬೇಕು" },
    { icon: "🏥", text: "ಆರೋಗ್ಯ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಬೇಕು" },
    { icon: "👩", text: "ಮಹಿಳೆಯರಿಗಾಗಿ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು" },
  ],
  ta: [
    { icon: "🌾", text: "நான் தமிழ்நாட்டு விவசாயி, 2 ஏக்கர் நிலம் உள்ளது" },
    { icon: "👩‍🎓", text: "உதவித்தொகை திட்டங்கள் தேவை" },
    { icon: "👴", text: "முதியோர், அரசு உதவி தேவை" },
    { icon: "💼", text: "சிறு தொழில் தொடங்க loan வேண்டும்" },
    { icon: "🏥", text: "சுகாதார திட்டங்களை தேட வேண்டும்" },
    { icon: "👩", text: "பெண்களுக்கான அரசு திட்டங்கள்" },
  ],
  bn: [
    { icon: "🌾", text: "আমি পশ্চিমবঙ্গের কৃষক, ২ একর জমি আছে" },
    { icon: "👩‍🎓", text: "বৃত্তির জন্য প্রকল্প দরকার" },
    { icon: "👴", text: "বয়স্ক নাগরিক, সরকারি সাহায্য দরকার" },
    { icon: "💼", text: "ছোট ব্যবসা শুরু করতে loan দরকার" },
    { icon: "🏥", text: "স্বাস্থ্য প্রকল্পগুলি খুঁজতে হবে" },
    { icon: "👩", text: "মহিলাদের জন্য সরকারি প্রকল্প" },
  ],
  mr: [
    { icon: "🌾", text: "मी महाराष्ट्रातील शेतकरी आहे, २ एकर जमीन आहे" },
    { icon: "👩‍🎓", text: "शिष्यवृत्तीसाठी योजना हवी आहे" },
    { icon: "👴", text: "ज्येष्ठ नागरिक, सरकारी मदत हवी आहे" },
    { icon: "💼", text: "छोटा व्यवसाय सुरू करायला loan हवे" },
    { icon: "🏥", text: "आरोग્ય योजना शोधायच्या आहेत" },
    { icon: "👩", text: "महिलांसाठी सरकारी योजना" },
  ],
  gu: [
    { icon: "🌾", text: "હું ગુજરાતનો ખેડૂત છું, ૨ એકર જમીન છે" },
    { icon: "👩‍🎓", text: "શિષ્યવૃત્તિ માટે યોજના જોઈએ છે" },
    { icon: "👴", text: "વૃદ્ધ નાગરિક, સરકારી મદદ જોઈએ" },
    { icon: "💼", text: "નાનો વ્યવસાય શરૂ કરવા loan જોઈએ" },
    { icon: "🏥", text: "સ્વાસ્થ્ય યોજનાઓ શોધવી છે" },
    { icon: "👩", text: "મહિલાઓ માટે સરકારી યોજનાઓ" },
  ],
}
