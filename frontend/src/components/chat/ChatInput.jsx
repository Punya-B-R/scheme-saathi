import { useState, useRef, useEffect } from 'react'
import { ArrowUp, Square } from 'lucide-react'

export default function ChatInput({ onSend, isLoading = false, disabled = false }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSubmit = () => {
    const text = value.trim()
    if (!text || isLoading || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = '44px'
    el.style.height = Math.min(el.scrollHeight, 5 * 24) + 'px'
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-4 shadow-[0_-4px_24px_-4px_rgba(0,0,0,0.06)]">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 rounded-2xl border border-gray-200 bg-gray-50/50 focus-within:border-blue-400 focus-within:bg-white transition-colors">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask about government schemes..."
            rows={1}
            disabled={disabled}
            className="flex-1 resize-none bg-transparent px-4 py-3 pr-12 text-sm leading-relaxed placeholder:text-gray-400 focus:outline-none disabled:opacity-50"
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading || disabled}
            className="absolute right-2 bottom-2 w-8 h-8 rounded-lg flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
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
        <p className="text-center text-[11px] text-gray-400 mt-2">
          Scheme Saathi can make mistakes. Verify information on official government portals.
        </p>
      </div>
    </div>
  )
}
