import { Mic, MicOff, Loader2 } from 'lucide-react'
import { useTranslation } from '../../utils/i18n'

export default function VoiceButton({
  isListening = false,
  isSupported = false,
  onStartListening,
  onStopListening,
  countdown = 5,
  disabled = false,
  language = 'en',
}) {
  const t = useTranslation(language)
  if (!isSupported) return null

  const handleClick = () => {
    if (disabled) return
    if (isListening) onStopListening?.()
    else onStartListening?.()
  }

  const title = isListening
    ? (language === 'hi' ? 'सुन रहा है... रोकने के लिए क्लिक करें' : 'Listening... click to stop')
    : (language === 'hi' ? 'बोलने के लिए क्लिक करें' : 'Click to speak')

  return (
    <div className="relative">
      {isListening && (
        <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-medium text-red-600 whitespace-nowrap">
          {t.sendingIn} {countdown}s...
        </div>
      )}

      <div className="relative">
        {isListening && (
          <>
            <span className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30" />
            <span
              className="absolute inset-0 scale-110 rounded-full bg-red-300 animate-ping opacity-20"
              style={{ animationDelay: '0.2s' }}
            />
            <span
              className="absolute inset-0 scale-125 rounded-full bg-red-200 animate-ping opacity-10"
              style={{ animationDelay: '0.4s' }}
            />
          </>
        )}

        <button
          type="button"
          onClick={handleClick}
          disabled={disabled}
          title={title}
          className={`relative rounded-full w-10 h-10 flex items-center justify-center transition-all ${
            isListening
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isListening ? (
            <MicOff className="w-4 h-4" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  )
}

