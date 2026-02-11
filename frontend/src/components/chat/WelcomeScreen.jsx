import { Sparkles } from 'lucide-react'
import { APP_NAME, QUICK_PROMPTS } from '../../utils/constants'

export default function WelcomeScreen({ onPromptClick }) {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-lg text-center">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-purple flex items-center justify-center mx-auto mb-5 shadow-lg shadow-primary-500/20">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Namaste!</h2>
        <p className="text-gray-500 mb-8 leading-relaxed">
          I'm {APP_NAME}. Tell me about yourself and I'll find government schemes you're eligible for.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {QUICK_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => onPromptClick(prompt)}
              className="text-left p-3.5 rounded-xl border border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50/50 transition-all text-sm text-gray-600 hover:text-gray-800 leading-relaxed"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
