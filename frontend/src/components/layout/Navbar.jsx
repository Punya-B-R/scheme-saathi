import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, ArrowRight, LogIn, UserPlus, LogOut } from 'lucide-react'
import { APP_NAME } from '../../utils/constants'
import { useAuth } from '../../context/AuthContext'

const NAV_LINKS = [
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#about', label: 'About' },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const isChat = pathname.startsWith('/chat')
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isAuthenticated, user, logout, loading } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => setMobileOpen(false), [pathname])

  if (isChat) return null

  return (
    <nav
      className={`
        sticky top-0 z-50 h-16
        transition-all duration-300 ease-out
        ${scrolled ? 'glass border-b border-gray-200/50 shadow-sm' : 'bg-transparent'}
      `}
    >
      <div className="max-w-7xl mx-auto h-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-full">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl gradient-blue-purple flex items-center justify-center shadow-lg shadow-blue-500/25">
              <span className="text-white font-bold text-sm">SS</span>
            </div>
            <span className="text-lg font-semibold text-gray-900 tracking-tight">{APP_NAME}</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100/80 transition-colors"
              >
                {link.label}
              </a>
            ))}
            <div className="w-px h-5 bg-gray-200 ml-2 mr-1" />
            {!loading && (
              isAuthenticated ? (
                <>
                  <span className="hidden sm:inline text-sm text-gray-600 truncate max-w-[120px]" title={user?.email}>{user?.email}</span>
                  <button
                    type="button"
                    onClick={() => logout()}
                    className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2 rounded-lg hover:bg-gray-100"
                  >
                    <LogOut className="w-4 h-4" />
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors px-3 py-2 rounded-lg hover:bg-gray-100"
                  >
                    <LogIn className="w-4 h-4" />
                    Log in
                  </Link>
                  <Link
                    to="/signup"
                    className="flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors px-3 py-2 rounded-lg hover:bg-primary-50"
                  >
                    <UserPlus className="w-4 h-4" />
                    Sign up
                  </Link>
                </>
              )
            )}
            <Link to="/chat" className="btn-primary text-sm px-5 py-2.5">
              Try for Free
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden w-10 h-10 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-100"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden glass border-t border-gray-200/50"
          >
            <div className="px-4 py-4 space-y-0">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="block py-3 text-sm font-medium text-gray-700 hover:text-gray-900 border-b border-gray-100 last:border-0"
                >
                  {link.label}
                </a>
              ))}
              {!loading && !isAuthenticated && (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMobileOpen(false)}
                    className="block py-3 text-sm font-medium text-gray-700 hover:text-gray-900 border-b border-gray-100"
                  >
                    Log in
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setMobileOpen(false)}
                    className="block py-3 text-sm font-medium text-primary-600 hover:text-primary-700 border-b border-gray-100"
                  >
                    Sign up
                  </Link>
                </>
              )}
              {!loading && isAuthenticated && (
                <button
                  type="button"
                  onClick={() => { logout(); setMobileOpen(false) }}
                  className="block w-full text-left py-3 text-sm font-medium text-gray-700 hover:text-gray-900 border-b border-gray-100"
                >
                  Log out
                </button>
              )}
              <div className="pt-4">
                <Link to="/chat" className="btn-primary w-full justify-center" onClick={() => setMobileOpen(false)}>
                  Start Chatting
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
