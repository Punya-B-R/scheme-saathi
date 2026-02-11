import { motion } from 'framer-motion'

const SUGGESTIONS = [
  { icon: '🌾', text: "I'm a farmer in Bihar" },
  { icon: '👩‍🎓', text: 'Student looking for scholarships' },
  { icon: '👴', text: 'Senior citizen, need welfare schemes' },
  { icon: '💼', text: 'Want to start a business' },
  { icon: '🏥', text: 'Looking for health schemes' },
  { icon: '👩', text: 'Women empowerment schemes' },
]

export default function WelcomeScreen({ onSuggestionClick }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="flex-1 flex items-center justify-center p-6"
    >
      <div className="max-w-lg w-full text-center">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-r from-blue-500 to-violet-500 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-500/20">
          <span className="text-white font-bold text-2xl">SS</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900">How can I help you today?</h2>
        <p className="mt-2 text-gray-500">
          I can help you discover government schemes you're eligible for.
        </p>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SUGGESTIONS.map((item, i) => (
            <motion.button
              key={item.text}
              type="button"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i }}
              onClick={() => onSuggestionClick(item.text)}
              className="flex items-center gap-3 text-left p-4 rounded-xl border border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50 transition-all shadow-sm"
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-sm font-medium text-gray-700">{item.text}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
