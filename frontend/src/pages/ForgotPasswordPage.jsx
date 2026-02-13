import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Sparkles, ArrowLeft, Mail } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { APP_NAME } from '../utils/constants'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const { resetPassword } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim()) {
      toast.error('Please enter your email address')
      return
    }
    setLoading(true)
    try {
      await resetPassword(email.trim())
      setSent(true)
      toast.success('Reset link sent! Check your inbox.')
    } catch (err) {
      const msg = err.message || 'Failed to send reset email. Please try again.'
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
          {sent ? (
            /* Success state */
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-7 h-7 text-green-600" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900 mb-2">Check your email</h1>
              <p className="text-gray-500 text-sm mb-1">
                We've sent a password reset link to
              </p>
              <p className="text-gray-900 font-medium text-sm mb-5">{email}</p>
              <p className="text-gray-400 text-xs mb-5">
                Didn't receive the email? Check your spam folder or{' '}
                <button
                  type="button"
                  onClick={() => setSent(false)}
                  className="text-primary-600 hover:underline font-medium"
                >
                  try again
                </button>
              </p>
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to login
              </Link>
            </div>
          ) : (
            /* Form state */
            <>
              <h1 className="text-xl font-semibold text-gray-900 mb-1">Forgot password?</h1>
              <p className="text-gray-500 text-sm mb-5">
                Enter your email and we'll send you a link to reset your password.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Email address
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-sm"
                    placeholder="you@example.com"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 rounded-lg bg-gradient-to-r from-primary-600 to-accent-purple text-white font-medium text-sm hover:opacity-95 disabled:opacity-60 transition"
                >
                  {loading ? 'Sending...' : 'Send reset link'}
                </button>
              </form>
              <p className="mt-5 text-center text-sm text-gray-500">
                <Link to="/login" className="inline-flex items-center gap-1 text-primary-600 font-medium hover:underline">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Back to login
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
