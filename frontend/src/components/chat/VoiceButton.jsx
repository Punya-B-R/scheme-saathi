import { useEffect, useState } from 'react'
import { Mic, Loader2 } from 'lucide-react'
import { useTranslation } from '../../utils/i18n'

export default function VoiceButton({
  isListening = false,
  isSupported = false,
  onStartListening,
  onStopListening,
  countdown = 5,
  disabled = false,
  language = 'en',
  transcript = '',
}) {
  const t = useTranslation(language)
  const [flashListening, setFlashListening] = useState(false)
  if (!isSupported) return null

  const handleClick = () => {
    if (disabled) return
    if (isListening) onStopListening?.()
    else onStartListening?.()
  }

  useEffect(() => {
    if (!isListening || !transcript) return
    setFlashListening(true)
    const timer = setTimeout(() => setFlashListening(false), 350)
    return () => clearTimeout(timer)
  }, [isListening, transcript])

  const title = isListening
    ? (language === 'hi' ? 'सुन रहा है... रोकने के लिए क्लिक करें' : 'Listening... click to stop')
    : (language === 'hi' ? 'बोलने के लिए क्लिक करें' : 'Click to speak')

  const countdownBg = flashListening
    ? 'bg-green-500'
    : countdown <= 1
      ? 'bg-red-600'
      : countdown <= 3
        ? 'bg-orange-500'
        : 'bg-gray-900'

  return (
    <div className="relative p-1">
      {isListening && (
        <div className={`absolute -top-3 left-1/2 -translate-x-1/2 text-[11px] font-mono text-white whitespace-nowrap px-2 py-0.5 rounded-full shadow-sm transition-colors duration-200 ${countdownBg}`}>
          {flashListening ? t.listening : `${countdown}s`}
          <span className={`absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[6px] border-l-transparent border-r-transparent ${
            flashListening
              ? 'border-t-green-500'
              : countdown <= 1
                ? 'border-t-red-600'
                : countdown <= 3
                  ? 'border-t-orange-500'
                  : 'border-t-gray-900'
          }`} />
        </div>
      )}

      <div className="relative">
        {isListening && (
          <>
            <span className="absolute -inset-1 rounded-full border-2 border-emerald-400 listening-ring" />
            <span
              className="absolute -inset-2 rounded-full border-2 border-emerald-300 listening-ring-delay-1"
            />
            <span
              className="absolute -inset-3 rounded-full border-[1.5px] border-emerald-200 listening-ring-delay-2"
            />
          </>
        )}

        <button
          type="button"
          onClick={handleClick}
          disabled={disabled}
          title={title}
          className={`relative rounded-full w-10 h-10 border border-gray-200 flex items-center justify-center transition-all duration-200 ${
            isListening
              ? 'bg-emerald-500 text-white hover:bg-emerald-600 scale-105'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  )
}

