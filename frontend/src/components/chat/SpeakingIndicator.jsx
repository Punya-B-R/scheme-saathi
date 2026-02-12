import { motion, AnimatePresence } from 'framer-motion'
import { Volume2, Square } from 'lucide-react'

const BARS = [1, 3, 5, 3, 1, 4, 2, 5]

export default function SpeakingIndicator({ isSpeaking = false, onStop }) {
  return (
    <AnimatePresence>
      {isSpeaking && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="absolute top-3 left-1/2 -translate-x-1/2 z-20 bg-white/95 border border-blue-100 shadow-md rounded-full px-4 py-2 flex items-center gap-3"
        >
          <Volume2 className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">Speaking...</span>
          <div className="flex items-end gap-0.5 h-4">
            {BARS.map((h, idx) => (
              <motion.span
                key={`${h}-${idx}`}
                className="w-1 rounded-full bg-blue-500"
                animate={{ scaleY: [0.4, 1, 0.5, 0.9] }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: idx * 0.06,
                  ease: 'easeInOut',
                }}
                style={{ height: `${h * 2}px`, transformOrigin: 'bottom' }}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={onStop}
            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100"
          >
            <Square className="w-3 h-3 fill-current" />
            Stop
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

