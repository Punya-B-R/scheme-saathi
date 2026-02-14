import { useState } from 'react'
import { Bell } from 'lucide-react'
import { subscribeToAlerts } from '../../services/api'

export default function SubscriptionPrompt({
  userContext = {},
  language = 'en',
  onDismiss,
  onSubscribed,
}) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('default') // default | loading | success | error | already_subscribed

  const state = userContext?.state || ''
  const occupation = userContext?.occupation || ''

  let subtitle = 'Get notified when new government schemes are added'
  if (state && occupation) {
    subtitle = `Get notified when new schemes for ${occupation}s in ${state} are added`
  } else if (state) {
    subtitle = `Get notified when new schemes in ${state} are added`
  } else if (occupation) {
    subtitle = `Get notified when new ${occupation} schemes are added`
  }

  const handleSubscribe = async () => {
    const trimmed = (email || '').trim()
    if (!trimmed || !trimmed.includes('@')) {
      setStatus('error')
      return
    }
    setLoading(true)
    setStatus('loading')
    try {
      const result = await subscribeToAlerts(
        trimmed,
        (name || '').trim(),
        userContext,
        language
      )
      if (result?.is_new_subscriber) {
        setStatus('success')
      } else {
        setStatus('already_subscribed')
      }
      if (result?.success) {
        onSubscribed?.()
      }
    } catch {
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const handleDismiss = () => {
    onDismiss?.()
  }

  if (status === 'success' || status === 'already_subscribed') {
    return (
      <div
        className="max-w-2xl mx-auto mt-4 p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-100 animate-in fade-in duration-300"
        role="alert"
      >
        <div className="flex items-center gap-2 text-emerald-700">
          <span className="text-xl">✓</span>
          <span className="font-semibold">
            {status === 'already_subscribed'
              ? "You're already subscribed"
              : "You're subscribed! 🎉"}
          </span>
        </div>
        {status === 'success' && (
          <p className="text-sm text-emerald-600 mt-1">
            We'll notify you at {email}
          </p>
        )}
        <button
          type="button"
          onClick={handleDismiss}
          className="mt-2 text-xs text-emerald-600 hover:underline"
        >
          Dismiss
        </button>
      </div>
    )
  }

  return (
    <div
      className="max-w-2xl mx-auto mt-4 p-4 rounded-2xl bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100"
      role="complementary"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
          <Bell className="w-5 h-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900">
            🔔 Stay Updated on New Schemes
          </h3>
          <p className="text-sm text-gray-600 mt-1">{subtitle}</p>

          <div className="mt-3 space-y-2">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full px-3 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
              disabled={loading}
            />
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name (optional)"
              className="w-full px-3 py-2 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
              disabled={loading}
            />
          </div>

          {status === 'error' && (
            <p className="text-sm text-red-600 mt-2">
              Something went wrong. Please check your email and try again.
            </p>
          )}

          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={handleSubscribe}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  Subscribing...
                </>
              ) : (
                'Get Alerts →'
              )}
            </button>
            <button
              type="button"
              onClick={handleDismiss}
              disabled={loading}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              No thanks
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
