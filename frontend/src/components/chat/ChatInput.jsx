import { useState, useRef, useEffect, useCallback } from 'react'
import { ArrowUp, Square } from 'lucide-react'
import { useTranslation } from '../../utils/i18n'
import useVoice from '../../hooks/useVoice'
import VoiceButton from './VoiceButton'

export default function ChatInput({
  onSend,
  isLoading = false,
  disabled = false,
  language = 'en',
  onVoiceReady,
}) {
  const [value, setValue] = useState('')
  const [countdown, setCountdown] = useState(5)
  const textareaRef = useRef(null)
  const valueRef = useRef('')
  const t = useTranslation(language)

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  useEffect(() => {
    valueRef.current = value
  }, [value])

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = '44px'
    el.style.height = `${Math.min(el.scrollHeight, 5 * 24)}px`
  }, [])

  const handleSubmit = useCallback(() => {
    const text = value.trim()
    if (!text || isLoading || disabled) return
    onSend(text, { fromVoice: false })
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
    }
  }, [value, isLoading, disabled, onSend])

  const handleFinalTranscript = useCallback((finalText) => {
    const text = (finalText || valueRef.current || '').trim()
    if (!text || isLoading || disabled) return
    onSend(text, { fromVoice: true })
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = '44px'
  }, [disabled, isLoading, onSend])

  const {
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoice({
    onTranscript: (text) => {
      setValue(text)
      requestAnimationFrame(resizeTextarea)
    },
    onFinalTranscript: handleFinalTranscript,
    language,
  })

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => resizeTextarea()

  useEffect(() => {
    if (!isListening) {
      setCountdown(5)
      return undefined
    }
    setCountdown(5)
    const interval = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)
    return () => clearInterval(interval)
  }, [isListening])

  useEffect(() => {
    if (isListening && transcript) setCountdown(5)
  }, [isListening, transcript])

  useEffect(() => {
    if (!onVoiceReady) return
    onVoiceReady({ speak, stopSpeaking, isSpeaking })
  }, [onVoiceReady, speak, stopSpeaking, isSpeaking])

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-4 shadow-[0_-4px_24px_-4px_rgba(0,0,0,0.06)]">
      <div className="max-w-3xl mx-auto">
        <div
          className={`relative flex items-end gap-2 rounded-2xl border transition-colors ${
            isListening
              ? 'border-red-400 bg-red-50/70 ring-2 ring-red-200'
              : 'border-gray-200 bg-gray-50/50 focus-within:border-blue-400 focus-within:bg-white'
          }`}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={isListening ? t.listening : t.inputPlaceholder}
            rows={1}
            disabled={disabled}
            className={`flex-1 resize-none bg-transparent px-4 py-3 pr-24 text-sm leading-relaxed placeholder:text-gray-400 focus:outline-none disabled:opacity-50 ${
              isListening ? 'text-red-700' : ''
            }`}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          {isListening && (
            <div className="absolute left-3 top-2.5 flex items-center gap-1">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs text-red-500">{t.listening}</span>
            </div>
          )}

          <div className="absolute right-2 bottom-2 flex items-center gap-2">
            <VoiceButton
              isListening={isListening}
              isSpeaking={isSpeaking}
              isSupported={isSupported}
              onStartListening={startListening}
              onStopListening={stopListening}
              countdown={countdown}
              disabled={isLoading || disabled}
              language={language}
            />

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading || disabled}
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
            style={{
              backgroundColor: value.trim() && !isLoading ? '#2563eb' : 'transparent',
              color: value.trim() && !isLoading ? 'white' : '#9ca3af',
            }}
          >
            {isLoading ? (
              <Square className="w-4 h-4 fill-current" />
            ) : (
              <ArrowUp className="w-4 h-4" />
            )}
          </button>
          </div>
        </div>
        <p className="text-center text-[11px] text-gray-400 mt-2">
          {t.disclaimer}
        </p>
      </div>
    </div>
  )
}
