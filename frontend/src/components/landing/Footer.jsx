import { Sparkles } from 'lucide-react'
import { APP_NAME } from '../../utils/constants'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 py-10 bg-gray-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-600 to-accent-purple flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-gray-700">{APP_NAME}</span>
          </div>
          <p className="text-xs text-gray-400 text-center">
            Data sourced from MyScheme.gov.in and official government portals. Not affiliated with any government body.
          </p>
        </div>
      </div>
    </footer>
  )
}
