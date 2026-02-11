import { Link } from 'react-router-dom'
import { Github, Twitter } from 'lucide-react'
import { APP_NAME, APP_TAGLINE } from '../../utils/constants'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-8">
          {/* Column 1 - Brand */}
          <div className="col-span-2 lg:col-span-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-blue-purple flex items-center justify-center">
                <span className="text-white font-bold text-xs">SS</span>
              </div>
              <span className="text-white font-semibold">{APP_NAME}</span>
            </div>
            <p className="mt-3 text-sm text-gray-400 max-w-xs">
              {APP_TAGLINE}
            </p>
            <div className="mt-4 flex items-center gap-3">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 transition-colors">
                <Github className="w-4 h-4" />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 transition-colors">
                <Twitter className="w-4 h-4" />
              </a>
            </div>
            <p className="mt-6 text-xs text-gray-500">© 2026 {APP_NAME}. All rights reserved.</p>
          </div>

          {/* Column 2 - Product */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-3">
              <li><a href="#how-it-works" className="text-sm hover:text-white transition-colors">How it Works</a></li>
              <li><a href="#features" className="text-sm hover:text-white transition-colors">Features</a></li>
              <li><Link to="/chat" className="text-sm hover:text-white transition-colors">Start Chatting</Link></li>
            </ul>
          </div>

          {/* Column 3 - Resources */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Resources</h4>
            <ul className="space-y-3">
              <li><a href="https://myscheme.gov.in" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors">MyScheme.gov.in</a></li>
              <li><a href="https://pmkisan.gov.in" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors">PM-KISAN Portal</a></li>
              <li><a href="https://digitalindia.gov.in" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors">Digital India</a></li>
            </ul>
          </div>

          {/* Column 4 - Languages */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Languages</h4>
            <p className="text-sm text-gray-400 mb-3">Available in:</p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-lg bg-gray-800 text-sm font-medium text-gray-300">English</span>
              <span className="px-3 py-1 rounded-lg bg-gray-800 text-sm font-medium text-gray-300">हिंदी</span>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <p className="text-center text-sm text-gray-500">
            Built with ❤️ for Bharat
          </p>
          <p className="text-center text-xs text-gray-600 mt-1">
            Powered by Google Gemini AI
          </p>
        </div>
      </div>
    </footer>
  )
}
