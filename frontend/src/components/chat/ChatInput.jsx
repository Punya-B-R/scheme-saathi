import { useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'

export default function ChatInput({ value, onChange, onSend, loading }) {
  const inputRef = useRef(null)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const handleInput = (e) => {
    e.target.style.height = '44px'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="max-w-3xl mx-auto flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Tell me about yourself or ask about a scheme..."
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder-gray-400 transition-shadow"
          style={{ minHeight: '44px', maxHeight: '120px' }}
        />
        <button
          onClick={onSend}
          disabled={!value.trim() || loading}
          className="w-11 h-11 rounded-xl bg-primary-600 text-white flex items-center justify-center hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </button>
      </div>
      <p className="text-center text-[10px] text-gray-400 mt-2 max-w-3xl mx-auto">
        Scheme Saathi may make mistakes. Verify information on official government portals.
      </p>
    </div>
  )
}
