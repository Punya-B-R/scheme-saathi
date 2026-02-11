import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import SchemeCard from './SchemeCard'

export default function Message({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`message-enter flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-primary-50 border border-primary-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-primary-600" />
        </div>
      )}

      <div className={`max-w-[85%] sm:max-w-[75%]`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white rounded-br-md'
              : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <ReactMarkdown
              className="prose prose-sm max-w-none prose-p:my-1.5 prose-li:my-0.5 prose-strong:text-gray-900 prose-a:text-primary-600 prose-a:no-underline hover:prose-a:underline"
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Scheme cards */}
        {!isUser && message.schemes && message.schemes.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.schemes.slice(0, 4).map((scheme, j) => (
              <SchemeCard key={scheme.scheme_id || j} scheme={scheme} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-gray-400 mt-1 block px-1">
          {message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })
            : ''}
        </span>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-4 h-4 text-gray-500" />
        </div>
      )}
    </div>
  )
}
