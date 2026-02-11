import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Wraps content that requires login. Redirects to /login with ?redirect=currentPath when not authenticated.
 */
export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
  const currentPath = location.pathname + location.search

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white">
        <div className="animate-pulse text-gray-500">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    const redirect = encodeURIComponent(currentPath)
    return <Navigate to={`/login?redirect=${redirect}`} replace state={{ from: location }} />
  }

  return children
}
