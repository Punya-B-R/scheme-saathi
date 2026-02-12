import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'

export default function useVoice({
  onTranscript,
  onFinalTranscript,
  language = 'en',
} = {}) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)

  const recognitionRef = useRef(null)
  const silenceTimerRef = useRef(null)
  const finalTextRef = useRef('')
  const liveTextRef = useRef('')
  const mountedRef = useRef(true)
  const onTranscriptRef = useRef(onTranscript)
  const onFinalTranscriptRef = useRef(onFinalTranscript)

  const isSupported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
  }, [])

  const stopListening = useCallback(() => {
    clearSilenceTimer()
    try {
      recognitionRef.current?.stop()
    } catch (_) {
      // no-op: stop can throw when already stopped
    }
    if (mountedRef.current) setIsListening(false)
  }, [clearSilenceTimer])

  const resetSilenceTimer = useCallback(() => {
    clearSilenceTimer()
    silenceTimerRef.current = setTimeout(() => {
      const text = (liveTextRef.current || '').trim()
      stopListening()
      if (text && onFinalTranscriptRef.current) onFinalTranscriptRef.current(text)
    }, 5000)
  }, [clearSilenceTimer, stopListening])

  useEffect(() => {
    onTranscriptRef.current = onTranscript
  }, [onTranscript])

  useEffect(() => {
    onFinalTranscriptRef.current = onFinalTranscript
  }, [onFinalTranscript])

  useEffect(() => {
    if (!isSupported) return undefined

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN'

    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const text = event.results[i][0].transcript
        if (event.results[i].isFinal) finalTranscript += text
        else interimTranscript += text
      }

      if (finalTranscript) {
        finalTextRef.current = `${finalTextRef.current} ${finalTranscript}`.trim()
      }

      const currentText = (finalTextRef.current || interimTranscript).trim()
      liveTextRef.current = currentText
      setTranscript(currentText)
      if (onTranscriptRef.current) onTranscriptRef.current(currentText)
      resetSilenceTimer()
    }

    recognition.onerror = (event) => {
      const message = `Voice error: ${event.error}`
      setError(message)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      try {
        recognition.abort()
      } catch (_) {
        // ignore
      }
    }
  }, [isSupported, language, resetSilenceTimer])

  const requestMicPermission = useCallback(async () => {
    if (!navigator?.mediaDevices?.getUserMedia) return true
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true })
      return true
    } catch (err) {
      if (err?.name === 'NotAllowedError') {
        setError(
          language === 'hi'
            ? 'माइक्रोफोन अनुमति अस्वीकृत। कृपया ब्राउज़र सेटिंग्स में अनुमति दें।'
            : 'Microphone access denied. Please allow microphone in browser settings.',
        )
      } else if (err?.name === 'NotFoundError') {
        setError(
          language === 'hi'
            ? 'माइक्रोफोन नहीं मिला। कृपया माइक्रोफोन कनेक्ट करें।'
            : 'No microphone found. Please connect a microphone.',
        )
      } else {
        setError(language === 'hi' ? 'माइक्रोफोन एक्सेस नहीं हो पा रहा है।' : 'Cannot access microphone.')
      }
      return false
    }
  }, [language])

  const startListening = useCallback(async () => {
    if (!isSupported) return
    const hasPermission = await requestMicPermission()
    if (!hasPermission) return

    setTranscript('')
    finalTextRef.current = ''
    liveTextRef.current = ''
    setError(null)
    setIsListening(true)
    try {
      recognitionRef.current?.start()
      resetSilenceTimer()
    } catch (err) {
      // start() can throw if already started; keep listening in that case
      if (String(err?.name || '').toLowerCase() === 'invalidstateerror') return
      setIsListening(false)
      setError(`Voice error: ${err?.message || 'cannot start recognition'}`)
    }
  }, [isSupported, requestMicPermission, resetSilenceTimer])

  const speak = useCallback(
    (text) => {
      if (!window?.speechSynthesis || !text) return

      window.speechSynthesis.cancel()
      const cleanText = String(text)
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/#{1,6}\s/g, '')
        .replace(/•\s/g, '')
        .replace(/\d+\.\s/g, '')
        .replace(/[₹]/g, language === 'hi' ? 'रुपये ' : 'rupees ')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/[\u{1F300}-\u{1FAFF}]/gu, '')
        .replace(/\n/g, '. ')
        .trim()

      if (!cleanText) return

      const chunkText = (input, maxLen = 220) => {
        const chunks = []
        let remaining = input
        while (remaining.length > maxLen) {
          let splitAt = remaining.lastIndexOf('.', maxLen)
          if (splitAt < 50) splitAt = remaining.lastIndexOf(' ', maxLen)
          if (splitAt < 20) splitAt = maxLen
          chunks.push(remaining.slice(0, splitAt + 1).trim())
          remaining = remaining.slice(splitAt + 1).trim()
        }
        if (remaining) chunks.push(remaining)
        return chunks.filter(Boolean)
      }

      const voices = window.speechSynthesis.getVoices()
      const preferredVoice =
        language === 'hi'
          ? voices.find(
              (v) =>
                v.lang === 'hi-IN' ||
                v.lang.startsWith('hi') ||
                v.name.toLowerCase().includes('hindi'),
            )
          : voices.find(
              (v) =>
                v.lang === 'en-IN' ||
                v.name.includes('India') ||
                v.name.includes('Ravi') ||
                v.name.includes('Heera'),
            )
      const chunks = chunkText(cleanText)
      if (!chunks.length) return

      let idx = 0
      setIsSpeaking(true)
      const speakNext = () => {
        if (idx >= chunks.length) {
          setIsSpeaking(false)
          return
        }
        const utterance = new SpeechSynthesisUtterance(chunks[idx])
        utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN'
        utterance.rate = 0.9
        utterance.pitch = 1.0
        utterance.volume = 1.0
        if (preferredVoice) utterance.voice = preferredVoice

        utterance.onend = () => {
          idx += 1
          speakNext()
        }
        utterance.onerror = () => {
          setIsSpeaking(false)
        }
        window.speechSynthesis.speak(utterance)
      }

      // If voices are not loaded yet, wait once then speak.
      if (!voices.length && typeof window.speechSynthesis.onvoiceschanged !== 'undefined') {
        window.speechSynthesis.onvoiceschanged = () => {
          speakNext()
          window.speechSynthesis.onvoiceschanged = null
        }
      } else {
        speakNext()
      }
    },
    [language],
  )

  const stopSpeaking = useCallback(() => {
    if (!window?.speechSynthesis) return
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }, [])

  useEffect(() => {
    if (!error) return
    toast.error(error)
  }, [error])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      clearSilenceTimer()
      try {
        recognitionRef.current?.abort()
      } catch (_) {
        // ignore
      }
      window?.speechSynthesis?.cancel()
    }
  }, [clearSilenceTimer])

  return {
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  }
}

