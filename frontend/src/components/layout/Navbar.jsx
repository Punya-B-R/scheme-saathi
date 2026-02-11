import { Link, useLocation } from 'react-router-dom'
import { Sparkles, MessageSquare, LogIn, UserPlus, LogOut } from 'lucide-react'
import { APP_NAME } from '../../utils/constants'
import Button from '../common/Button'
import { useAuth } from '../../context/AuthContext'

export default function Navbar() {
  const { pathname } = useLocation()
  const isChat = pathname.startsWith('/chat')
  const { isAuthenticated, user, logout, loading } = useAuth()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-gray-200/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-accent-purple flex items-center justify-center shadow-lg shadow-primary-600/20 group-hover:shadow-primary-600/40 transition-shadow">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">{APP_NAME}</span>
          </Link>

          <div className="flex items-center gap-3">
            {!isChat && (
              <>
                <a href="#features" className="hidden sm:block text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2">Features</a>
                <a href="#how-it-works" className="hidden sm:block text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2">How it Works</a>
              </>
            )}
            {!loading && (
              <>
                {isAuthenticated ? (
                  <>
                    <span className="hidden sm:inline text-sm text-gray-600 truncate max-w-[120px]" title={user?.email}>{user?.email}</span>
                    <button
                      type="button"
                      onClick={() => logout()}
                      className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2 rounded-lg hover:bg-gray-100"
                    >
                      <LogOut className="w-4 h-4" />
                      <span className="hidden sm:inline">Log out</span>
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2 rounded-lg hover:bg-gray-100"
                    >
                      <LogIn className="w-4 h-4" />
                      <span className="hidden sm:inline">Log in</span>
                    </Link>
                    <Link to="/signup">
                      <Button variant="gradient" size="sm">
                        <UserPlus className="w-4 h-4" />
                        <span className="hidden sm:inline">Sign up</span>
                      </Button>
                    </Link>
                  </>
                )}
              </>
            )}
            <Link to="/chat">
              <Button variant={isChat ? 'secondary' : 'gradient'} size="sm">
                <MessageSquare className="w-4 h-4" />
                <span className="hidden sm:inline">{isChat ? 'New Chat' : 'Start Chat'}</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
