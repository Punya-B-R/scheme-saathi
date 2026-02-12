import { motion } from 'framer-motion'
import { useTranslation } from '../../utils/i18n'

export default function TypingIndicator({ language = 'en' }) {
  const t = useTranslation(language)
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start gap-3 message-enter"
    >
      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-violet-500 flex items-center justify-center flex-shrink-0 shadow-sm">
        <span className="text-white font-bold text-[10px]">SS</span>
      </div>
      <div className="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-tl-sm bg-white border border-gray-100 shadow-sm">
        <span className="typing-dot w-2 h-2 rounded-full bg-gray-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-gray-400" />
        <span className="typing-dot w-2 h-2 rounded-full bg-gray-400" />
      </div>
      <p className="text-xs text-gray-400 mt-1 ml-11">{t.thinking}</p>
    </motion.div>
  )
}
