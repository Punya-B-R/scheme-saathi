import { ExternalLink, MapPin, Tag } from 'lucide-react'
import Badge from '../common/Badge'

export default function SchemeCard({ scheme }) {
  if (!scheme) return null

  const name = scheme.scheme_name || 'Unknown Scheme'
  const category = scheme.category || ''
  const benefits = scheme.benefits
  const summary = typeof benefits === 'object' ? (benefits?.summary || '') : (benefits || '')
  const url = scheme.source_url || scheme.official_website || ''
  const elig = scheme.eligibility_criteria || {}
  const state = typeof elig === 'object' ? (elig.state || 'All India') : 'All India'

  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white hover:border-primary-200 hover:shadow-sm transition-all group">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-semibold text-sm text-gray-900 leading-snug">{name}</h4>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-2">
        {category && <Badge color="blue">{category}</Badge>}
        {state && state !== 'All India' && (
          <Badge color="green">
            <MapPin className="w-3 h-3 mr-0.5" />
            {state}
          </Badge>
        )}
      </div>

      {summary && (
        <p className="text-xs text-gray-500 leading-relaxed mb-3 line-clamp-2">{summary}</p>
      )}

      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
        >
          Apply / Learn More <ExternalLink className="w-3 h-3" />
        </a>
      )}
    </div>
  )
}
