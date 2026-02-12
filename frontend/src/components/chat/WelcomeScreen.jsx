import { motion } from 'framer-motion'
import { SUGGESTIONS } from '../../utils/constants'
import { useTranslation } from '../../utils/i18n'

export default function WelcomeScreen({ onSuggestionClick, language = 'en' }) {
  const t = useTranslation(language)
  const suggestions = SUGGESTIONS[language] || SUGGESTIONS.en

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
        <h2 className="text-2xl font-bold text-gray-900">{t.welcomeTitle}</h2>
        <p className="mt-2 text-gray-500">
          {t.welcomeSubtitle}
        </p>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {suggestions.map((item, i) => (
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
