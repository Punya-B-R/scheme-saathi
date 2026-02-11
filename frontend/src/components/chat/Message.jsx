import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import SchemeCard from './SchemeCard'

const ASSISTANT_NAME = 'Scheme Saathi'

export default function Message({ message, isLatest }) {
  const isUser = message.role === 'user'

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
            <div className="prose prose-sm max-w-none prose-p:my-1.5 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-strong:font-semibold prose-strong:text-gray-900 prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Scheme cards (AI only) */}
        {!isUser && message.schemes?.length > 0 && (
          <div className="mt-3 w-full max-w-2xl space-y-2">
            <p className="text-xs font-semibold text-gray-500 mb-2">Schemes found for you:</p>
            {message.schemes.slice(0, 5).map((scheme, i) => (
              <SchemeCard key={scheme.scheme_id || i} scheme={scheme} />
            ))}
          </div>
        )}

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
