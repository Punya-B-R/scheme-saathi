import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MapPin, Banknote, FileText, ExternalLink, ChevronDown } from 'lucide-react'
import { useTranslation } from '../../utils/i18n'

const CATEGORY_COLORS = {
  agriculture: 'bg-emerald-500',
  'agriculture, rural & environment': 'bg-emerald-500',
  education: 'bg-blue-500',
  'education & learning': 'bg-blue-500',
  healthcare: 'bg-rose-500',
  'health & wellness': 'bg-rose-500',
  'social welfare': 'bg-violet-500',
  'social welfare & empowerment': 'bg-violet-500',
  business: 'bg-amber-500',
  'business & entrepreneurship': 'bg-amber-500',
  'skills & employment': 'bg-teal-500',
  'banking, financial services and insurance': 'bg-indigo-500',
  'sports & culture': 'bg-orange-500',
  'public safety': 'bg-yellow-500',
  'public safety, law & justice': 'bg-yellow-500',
  'women and child': 'bg-pink-500',
  'housing & shelter': 'bg-cyan-500',
  'science, it & communications': 'bg-purple-500',
  'transport & infrastructure': 'bg-slate-500',
  'travel & tourism': 'bg-sky-500',
  'utility & sanitation': 'bg-lime-500',
  'senior citizens': 'bg-amber-600',
  default: 'bg-gray-500',
}

function getCategoryColor(category) {
  if (!category) return CATEGORY_COLORS.default
  const key = (category || '').toLowerCase()
  return CATEGORY_COLORS[key] || CATEGORY_COLORS.default
}

function localizeBenefitType(benefitType, language) {
  if (language !== 'hi' || !benefitType) return benefitType
  const map = {
    Scholarship: 'छात्रवृत्ति',
    Loan: 'ऋण',
    Pension: 'पेंशन',
    Insurance: 'बीमा',
    Subsidy: 'सब्सिडी',
    'Skill Training': 'कौशल प्रशिक्षण',
    'Financial Assistance': 'वित्तीय सहायता',
    'Maternity Benefit': 'मातृत्व लाभ',
    'Marriage Assistance': 'विवाह सहायता',
    Housing: 'आवास',
    Healthcare: 'स्वास्थ्य सहायता',
    'Food/Essentials': 'खाद्य/आवश्यक सहायता',
    'Travel Concession': 'यात्रा रियायत',
    'Startup Fund': 'स्टार्टअप फंड',
    Rehabilitation: 'पुनर्वास',
    'Legal Aid': 'कानूनी सहायता',
  }
  return map[benefitType] || benefitType
}

export default function SchemeCard({ scheme, language = 'en' }) {
  const [expanded, setExpanded] = useState(false)
  const t = useTranslation(language)

  if (!scheme) return null

  const name = scheme.scheme_name || 'Unknown Scheme'
  const category = scheme.category || ''
  const elig = scheme.eligibility_criteria || {}
  const rawElig = typeof elig === 'object' ? (elig.raw_eligibility_text || '') : ''
  const state = typeof elig === 'object' ? (elig.state || '') : ''
  const displayState = state.toLowerCase().includes('all india') ? t.allIndia : state
  const benefitType = typeof (scheme.benefits) === 'object' ? (scheme.benefits?.benefit_type || '') : ''
  const benefitTypeLabel = localizeBenefitType(benefitType, language)
  const benefits = scheme.benefits || {}
  const benefitSummary = typeof benefits === 'object' ? (benefits.summary || benefits.raw_benefits_text || '') : String(benefits)
  const financialBenefit = typeof benefits === 'object' ? (benefits.financial_benefit || '') : ''
  const frequency = typeof benefits === 'object' ? (benefits.frequency || '') : ''
  const docs = scheme.required_documents
  const docCount = Array.isArray(docs) ? docs.length : 0
  const process = scheme.application_process
  const processSteps = Array.isArray(process) ? process : []
  const url = scheme.source_url || scheme.official_website || ''

  const dotColor = getCategoryColor(category)

  return (
    <div
      className="rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md hover:border-blue-200 transition-all overflow-hidden"
      role="button"
      tabIndex={0}
      onClick={() => setExpanded(!expanded)}
      onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${dotColor}`} />
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-gray-900 text-sm leading-snug">{name}</h4>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {category && (
                <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-gray-100 text-gray-600">
                  {category}
                </span>
              )}
              {benefitType && benefitType !== 'Other' && (
                <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-50 text-blue-600">
                  {benefitTypeLabel}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Benefits row */}
        {(financialBenefit || benefitSummary) && (
          <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
            <Banknote className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <span className="truncate">{financialBenefit || benefitSummary.substring(0, 80)}</span>
            {frequency && (
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-500 flex-shrink-0">
                {frequency}
              </span>
            )}
          </div>
        )}

        {/* Eligibility preview */}
        {rawElig && !expanded && (
          <div className="mt-2">
            <p className="text-[11px] font-medium text-gray-500 mb-0.5">{t.eligibility}:</p>
            <p className="text-xs text-gray-600 line-clamp-2">{rawElig.substring(0, 120)}{rawElig.length > 120 ? '...' : ''}</p>
          </div>
        )}

        {/* State + info row */}
        <div className="mt-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {state && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <MapPin className="w-3.5 h-3.5" />
                {displayState}
              </span>
            )}
            <span className="text-[11px] text-gray-400 flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {docCount} {language === 'hi' ? t.documents : 'docs needed'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                {t.applyNow}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
            <span className="text-[11px] text-gray-500">
              {expanded ? t.showLess : t.showMore}
            </span>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </div>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-3 border-t border-gray-100 space-y-3 bg-gray-50/50">
              {rawElig && (
                <div>
                  <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">{t.eligibility}</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{rawElig}</p>
                </div>
              )}

              {(financialBenefit || benefitSummary) && (
                <div>
                  <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">Benefits</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{benefitSummary || financialBenefit}</p>
                </div>
              )}

              {Array.isArray(docs) && docs.length > 0 && (
                <div>
                  <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">{t.documents}</p>
                  <ul className="list-disc list-inside text-xs text-gray-700 space-y-0.5">
                    {docs.map((d, i) => (
                      <li key={i}>{typeof d === 'object' ? d.document_name : d}</li>
                    ))}
                  </ul>
                </div>
              )}

              {processSteps.length > 0 && (
                <div>
                  <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">{t.applyNow}</p>
                  <ol className="list-decimal list-inside text-xs text-gray-700 space-y-1">
                    {processSteps.map((step, i) => (
                      <li key={i}>{typeof step === 'object' ? (step.step ?? step) : step}</li>
                    ))}
                  </ol>
                </div>
              )}

              {url && (
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
                >
                  {t.viewDetails}
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
