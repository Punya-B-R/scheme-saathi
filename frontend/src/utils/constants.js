export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const APP_NAME = 'Scheme Saathi'
export const APP_TAGLINE = 'Your AI Guide to Government Schemes'
export const APP_DESCRIPTION = "Discover government schemes you're eligible for through AI-powered conversations. Simple, fast, and free."

export const FEATURES = [
  {
    title: 'AI-Powered Discovery',
    description: 'Natural conversations to find schemes that match your exact situation',
    icon: 'bot',
  },
  {
    title: '3,700+ Government Schemes',
    description: 'Comprehensive database covering agriculture, education, healthcare, and more',
    icon: 'database',
  },
  {
    title: 'Instant Eligibility Check',
    description: 'Know if you qualify before applying, saving time and effort',
    icon: 'check',
  },
  {
    title: 'Multi-Language Support',
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
  { value: '3,700+', label: 'Government Schemes' },
  { value: '29', label: 'States Covered' },
  { value: '15', label: 'Categories' },
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

export const QUICK_PROMPTS = [
  "I'm a farmer in Bihar with 2 acres of land",
  "Show me scholarships for SC/ST students",
  "What pension schemes exist for senior citizens?",
  "I'm a woman entrepreneur looking for loans",
]
