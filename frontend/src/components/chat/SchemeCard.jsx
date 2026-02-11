import { useState } from 'react'
import { MapPin, Banknote, FileText, ExternalLink } from 'lucide-react'

const CATEGORY_COLORS = {
  agriculture: 'bg-emerald-500',
  education: 'bg-blue-500',
  healthcare: 'bg-rose-500',
  'health & wellness': 'bg-rose-500',
  'social welfare': 'bg-violet-500',
  'social welfare & empowerment': 'bg-violet-500',
  business: 'bg-amber-500',
  'business & entrepreneurship': 'bg-amber-500',
  'public safety': 'bg-yellow-500',
  'women and child': 'bg-pink-500',
  default: 'bg-gray-500',
}

function getCategoryColor(category) {
  if (!category) return CATEGORY_COLORS.default
  const key = (category || '').toLowerCase()
  return CATEGORY_COLORS[key] || CATEGORY_COLORS.default
}

function getMatchColor(score) {
  if (score == null) return 'bg-gray-100 text-gray-600'
  if (score >= 70) return 'bg-emerald-100 text-emerald-700'
  if (score >= 50) return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-600'
}

export default function SchemeCard({ scheme, matchScore }) {
  const [expanded, setExpanded] = useState(false)

  if (!scheme) return null

  const name = scheme.scheme_name || 'Unknown Scheme'
  const category = scheme.category || ''
  const elig = scheme.eligibility_criteria || {}
  const rawElig = typeof elig === 'object' ? (elig.raw_eligibility_text || '') : ''
  const state = typeof elig === 'object' ? (elig.state || '') : ''
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
  const matchClass = getMatchColor(matchScore)

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
              {matchScore != null && (
                <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${matchClass}`}>
                  {matchScore}% match
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

        {/* Eligibility (collapsed) */}
        {rawElig && (
          <div className="mt-2">
            <p className="text-[11px] font-medium text-gray-500 mb-0.5">Who can apply:</p>
            <p className="text-xs text-gray-600 line-clamp-2">{expanded ? rawElig : rawElig.substring(0, 100)}{rawElig.length > 100 && !expanded ? '…' : ''}</p>
            {rawElig.length > 100 && (
              <span className="text-xs text-blue-600 mt-0.5 inline-block">{expanded ? 'Click to collapse' : 'Click to expand'}</span>
            )}
          </div>
        )}

        {/* State */}
        {state && (
          <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
            <MapPin className="w-3.5 h-3.5" />
            {state}
          </div>
        )}

        {/* Footer */}
        <div className="mt-3 flex items-center justify-between pt-3 border-t border-gray-100">
          <span className="text-[11px] text-gray-400 flex items-center gap-1">
            <FileText className="w-3 h-3" />
            {docCount} required docs
          </span>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View Details
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100 space-y-3">
          {rawElig && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase mb-1">Eligibility</p>
              <p className="text-xs text-gray-600">{rawElig}</p>
            </div>
          )}
          {Array.isArray(docs) && docs.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase mb-1">Required documents</p>
              <ul className="list-disc list-inside text-xs text-gray-600 space-y-0.5">
                {docs.map((d, i) => (
                  <li key={i}>{typeof d === 'object' ? d.document_name : d}</li>
                ))}
              </ul>
            </div>
          )}
          {processSteps.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold text-gray-500 uppercase mb-1">Application process</p>
              <ol className="list-decimal list-inside text-xs text-gray-600 space-y-1">
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
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 text-blue-700 text-sm font-medium hover:bg-blue-100"
            >
              Open official website
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      )}
    </div>
  )
}
