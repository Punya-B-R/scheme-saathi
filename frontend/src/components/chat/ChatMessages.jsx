import { useEffect, useRef } from 'react'
import Message from './Message'
import TypingIndicator from './TypingIndicator'
import WelcomeScreen from './WelcomeScreen'
import SubscriptionPrompt from './SubscriptionPrompt'

export default function ChatMessages({
  messages = [],
  isLoading = false,
  onSuggestionClick,
  language = 'en',
  onSpeakMessage,
  isSpeaking = false,
  showSubscriptionPrompt = false,
  extractedContext = {},
  onSubscriptionDismiss,
  onSubscribed,
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return <WelcomeScreen onSuggestionClick={onSuggestionClick} language={language} />
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin bg-gray-50/30">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.map((msg, i) => (
          <Message
            key={msg.id || i}
            message={msg}
            isLatest={i === messages.length - 1}
            language={language}
            onSpeak={onSpeakMessage}
            isSpeaking={isSpeaking}
          />
        ))}
        {isLoading && <TypingIndicator language={language} />}
        {showSubscriptionPrompt && !isLoading && (
          <SubscriptionPrompt
            userContext={extractedContext}
            language={language}
            onDismiss={onSubscriptionDismiss}
            onSubscribed={onSubscribed}
          />
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
