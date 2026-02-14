import { useState, useRef, useEffect, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
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
  const [ringFlashGreen, setRingFlashGreen] = useState(false)
  const [transcriptPulse, setTranscriptPulse] = useState(false)
  const textareaRef = useRef(null)
  const valueRef = useRef('')
  const previousTranscriptRef = useRef('')
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
    if (!isListening) {
      setRingFlashGreen(false)
      setTranscriptPulse(false)
      previousTranscriptRef.current = ''
      return
    }
    const previous = previousTranscriptRef.current
    if (transcript && transcript !== previous) {
      setRingFlashGreen(true)
      setTranscriptPulse(true)
      const ringTimer = setTimeout(() => setRingFlashGreen(false), 300)
      const textTimer = setTimeout(() => setTranscriptPulse(false), 150)
      previousTranscriptRef.current = transcript
      return () => {
        clearTimeout(ringTimer)
        clearTimeout(textTimer)
      }
    }
    previousTranscriptRef.current = transcript
    return undefined
  }, [isListening, transcript])

  useEffect(() => {
    if (!onVoiceReady) return
    onVoiceReady({ speak, stopSpeaking, isSpeaking })
  }, [onVoiceReady, speak, stopSpeaking, isSpeaking])

  return (
    <div className="relative border-t border-gray-200 bg-white px-4 py-4 shadow-[0_-4px_24px_-4px_rgba(0,0,0,0.06)]">
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            className="absolute left-0 right-0 -top-10 z-10 flex justify-center pointer-events-none"
          >
            <div className="flex items-center gap-3 bg-white border border-emerald-200 rounded-full px-4 py-2 shadow-lg shadow-emerald-100 mx-auto w-fit">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {transcript ? (
                <span className="text-sm text-gray-700 max-w-xs truncate">"{transcript}"</span>
              ) : (
                <span className="text-sm text-gray-500">Listening for your voice...</span>
              )}
              {transcript && (
                <span className="text-xs text-gray-400 shrink-0">{countdown}s</span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="max-w-3xl mx-auto">
        <div
          className={`relative flex items-end gap-2 rounded-2xl border transition-all duration-200 ${
            isListening
              ? `border-emerald-300 bg-emerald-50 ring-2 ring-offset-1 ${
                ringFlashGreen ? 'ring-emerald-400' : 'ring-emerald-300'
              }`
              : 'border-gray-200 bg-gray-50/50 focus-within:border-blue-400 focus-within:bg-white'
          }`}
        >
          {isListening && (
            <div className="absolute top-2 left-3 flex items-center gap-1.5 pointer-events-none">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-emerald-600 font-medium">
                {t.listening}
              </span>
            </div>
          )}

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={isListening ? 'Speak now...' : t.inputPlaceholder}
            rows={1}
            disabled={disabled}
            className={`flex-1 resize-none bg-transparent px-4 py-3 pr-24 text-sm leading-relaxed placeholder:text-gray-400 focus:outline-none disabled:opacity-50 transition-opacity duration-150 ${
              isListening ? 'pt-7 text-gray-800' : ''
            } ${
              transcriptPulse ? 'opacity-80' : 'opacity-100'
            }`}
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />

          <div className="absolute right-3 bottom-2 flex items-center gap-2">
            <VoiceButton
              isListening={isListening}
              isSpeaking={isSpeaking}
              isSupported={isSupported}
              onStartListening={startListening}
              onStopListening={stopListening}
              countdown={countdown}
              disabled={isLoading || disabled}
              language={language}
              transcript={transcript}
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
        <div className="mt-2 min-h-4">
          {isListening ? (
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-1.5">
                <div className="flex items-end gap-0.5 h-4">
                  {[2, 4, 3, 5, 2, 4, 3, 2, 4, 5].map((height, i) => (
                    <div
                      key={i}
                      className="w-0.5 bg-emerald-400 rounded-full"
                      style={{
                        height: `${height * 2}px`,
                        animation: 'soundBar 0.8s ease-in-out infinite',
                        animationDelay: `${i * 0.08}s`,
                      }}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-600">
                  Speak clearly • Auto-sends after silence
                </span>
              </div>
              <span className="text-xs text-gray-400">
                {transcript.length > 0 ? `${transcript.trim().split(/\s+/).length} words` : ''}
              </span>
            </div>
          ) : (
            <p className="text-center text-[11px] text-gray-400">{t.disclaimer}</p>
          )}
        </div>
      </div>
    </div>
  )
}
