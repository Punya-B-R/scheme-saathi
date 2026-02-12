import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Sparkles, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { APP_NAME } from '../utils/constants'

export default function ResetPasswordPage() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const { updatePassword } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!password) {
      toast.error('Please enter a new password')
      return
    }
    if (password.length < 6) {
      toast.error('Password should be at least 6 characters')
      return
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await updatePassword(password)
      setDone(true)
      toast.success('Password updated successfully!')
      // Auto-redirect to chat after a short delay
      setTimeout(() => navigate('/chat', { replace: true }), 2500)
    } catch (err) {
      const msg = err.message || 'Failed to update password. The link may have expired.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-primary-50 to-white px-4 overflow-hidden">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-600 to-accent-purple flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-semibold text-gray-900">{APP_NAME}</span>
        </div>
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 px-7 py-6">
          {done ? (
            /* Success state */
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-7 h-7 text-green-600" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900 mb-2">Password updated</h1>
              <p className="text-gray-500 text-sm mb-5">
                Your password has been changed. Redirecting you to chat...
              </p>
              <Link
                to="/chat"
                className="text-sm font-medium text-primary-600 hover:underline"
              >
                Go to chat now
              </Link>
            </div>
          ) : (
            /* Form state */
            <>
              <h1 className="text-xl font-semibold text-gray-900 mb-1">Set new password</h1>
              <p className="text-gray-500 text-sm mb-5">
                Enter your new password below.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    New password
                  </label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    autoFocus
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-sm"
                    placeholder="Min 6 characters"
                  />
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                    Confirm new password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-sm"
                    placeholder="Re-enter password"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-accent-purple text-white font-medium text-sm hover:opacity-95 disabled:opacity-60 transition"
                >
                  {loading ? 'Updating...' : 'Update password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
