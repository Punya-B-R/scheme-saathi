import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { APP_NAME } from '../../utils/constants'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200/60 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-600 to-violet-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-bold text-gray-800">{APP_NAME}</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6 text-[13px] text-gray-500">
            <a href="#features" className="hover:text-gray-700 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-gray-700 transition-colors">How it Works</a>
            <Link to="/chat" className="hover:text-gray-700 transition-colors">Chat</Link>
          </div>

          {/* Disclaimer */}
          <p className="text-[11px] text-gray-400 text-center md:text-right max-w-xs">
            Data from MyScheme.gov.in and official portals. Not affiliated with any government body.
          </p>
        </div>
      </div>
    </footer>
  )
}
