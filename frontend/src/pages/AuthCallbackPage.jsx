import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { APP_NAME } from '../utils/constants'
import { useAuth } from '../context/AuthContext'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const { isAuthenticated, loading } = useAuth()
  const redirected = useRef(false)

  useEffect(() => {
    if (redirected.current) return

    if (!loading && isAuthenticated) {
      redirected.current = true
      navigate('/chat', { replace: true })
      return
    }

   
    const timer = setTimeout(() => {
      if (!redirected.current) {
        redirected.current = true
        navigate('/login', { replace: true })
      }
    }, 8000)

    return () => clearTimeout(timer)
  }, [loading, isAuthenticated, navigate])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-600 to-accent-purple flex items-center justify-center shadow-lg shadow-blue-500/25 animate-pulse">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">{APP_NAME}</h2>
        <p className="text-sm text-gray-500">Completing sign in...</p>
        <div className="mt-2 w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    </div>
  )
}
