import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { Volume2, VolumeX } from 'lucide-react'
import SchemeCard from './SchemeCard'
import { useTranslation } from '../../utils/i18n'

const ASSISTANT_NAME = 'Scheme Saathi'

const doesResponseMentionSchemes = (content) => {
  if (!content || typeof content !== 'string') return false
  const schemeIndicators = [
    'scheme', 'schemes', 'yojana', 'yojnaa',
    'benefit', 'benefits', 'eligible', 'eligibility',
    'qualify', 'qualified', 'entitled', 'entitlement',
    'apply', 'application', 'register', 'enroll',
    'found for you', 'here are', 'following',
    'these are', 'i found', "i've found",
    'matches', 'matching', 'matched',
    'options for you', 'programs', 'initiatives',
    'for your profile', 'based on your',
    'results', 'recommendations',
    '₹', 'rupees', 'lakh', 'per month',
    'per year', 'annually', 'monthly',
    'financial assistance', 'subsidy', 'pension',
    'scholarship', 'loan', 'grant',
    'योजना', 'योजनाएं', 'पात्र', 'लाभ',
    'आवेदन', 'मिलेगा', 'मिलेंगे',
    'सहायता', 'छात्रवृत्ति',
  ]
  const lowerContent = content.toLowerCase()
  return schemeIndicators.some((ind) => lowerContent.includes(ind.toLowerCase()))
}

export default function Message({
  message,
  isLatest,
  language = 'en',
  onSpeak,
  isSpeaking = false,
}) {
  // DEBUG: Message component
  console.log('DEBUG MSG 1 - message.role:', message.role)
  console.log('DEBUG MSG 2 - message.schemes:', message.schemes)
  console.log('DEBUG MSG 3 - schemes length:', message.schemes?.length)

  const isUser = message.role === 'user'
  const t = useTranslation(language)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} message-enter`}
      data-is-latest={isLatest}
    >
      {/* AI avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-violet-500 flex items-center justify-center flex-shrink-0 shadow-sm">
          <span className="text-white font-bold text-[10px]">SS</span>
        </div>
      )}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-[75%]`}>
        {!isUser && (
          <p className="text-[11px] font-medium text-gray-500 mb-0.5 ml-1">{ASSISTANT_NAME}</p>
        )}
        <div className={`${!isUser ? 'group relative' : ''}`}>
          <div
            className={
              isUser
                ? 'message-bubble-user'
                : 'message-bubble-ai'
            }
          >
            {isUser ? (
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none prose-p:my-1.5 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-strong:font-semibold prose-strong:text-gray-900">
                <ReactMarkdown
                  components={{
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline underline-offset-2 hover:text-blue-800 break-all"
                      >
                        {children}
                      </a>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
          {!isUser && (
            <button
              type="button"
              onClick={() => onSpeak?.(message.content)}
              className="absolute bottom-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-100 hover:bg-gray-200 rounded-full p-1.5"
              title={isSpeaking ? 'Stop speaking' : 'Listen to this message'}
            >
              {isSpeaking ? (
                <VolumeX className="w-3 h-3 text-gray-600" />
              ) : (
                <Volume2 className="w-3 h-3 text-gray-600" />
              )}
            </button>
          )}
        </div>

        {/* Show scheme cards when schemes exist. Trust backend (only returns schemes when confident). */}
        {!isUser && (() => {
          const schemeList = Array.isArray(message.schemes) ? message.schemes : []
          if (
            schemeList.length > 0 &&
            (doesResponseMentionSchemes(message.content) || schemeList.length > 0)
          ) {
            return (
              <div className="mt-3 w-full max-w-2xl space-y-2">
                <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                  {t.schemesFound}
                </p>
                {schemeList.slice(0, 20).map((scheme, i) => (
                  <SchemeCard key={scheme.scheme_id || `s-${i}`} scheme={scheme} language={language} />
                ))}
              </div>
            )
          }
          return null
        })()}

        {message.timestamp && (
          <p className={`text-[10px] text-gray-400 mt-1 ${isUser ? '' : 'ml-1'}`}>
            {new Date(message.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
          </p>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 text-gray-600 text-xs font-semibold">
          U
        </div>
      )}
    </motion.div>
  )
}
