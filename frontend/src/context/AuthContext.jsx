import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { STORAGE_KEYS } from '../utils/constants'
import { clearAllChats } from '../services/storage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setTokenState] = useState(null)
  const [loading, setLoading] = useState(true)

  const setToken = useCallback((newToken) => {
    if (newToken) {
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, newToken)
      setTokenState(newToken)
    } else {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.AUTH_USER)
      setTokenState(null)
      setUser(null)
    }
  }, [])

  const updateUserFromSession = useCallback(
    (session) => {
      if (!session?.user) {
        setUser(null)
        setToken(null)
        return
      }
      const u = session.user
      const userObj = { id: u.id, email: u.email ?? '' }
      setUser(userObj)
      setTokenState(session.access_token)
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, session.access_token)
      localStorage.setItem(STORAGE_KEYS.AUTH_USER, JSON.stringify(userObj))
      // Clear shared localStorage chats when authenticated (chats are now in Supabase DB)
      clearAllChats()
    },
    [setToken]
  )

  useEffect(() => {
    let mounted = true

    const initSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession()
        if (!mounted) return
        if (error) {
          
          await supabase.auth.signOut().catch(() => {})
          setUser(null)
          setToken(null)
          setLoading(false)
          return
        }
        if (session) updateUserFromSession(session)
      } catch (_) {
        
        await supabase.auth.signOut().catch(() => {})
        if (mounted) setToken(null)
      } finally {
        if (mounted) setLoading(false)
      }
    }

    initSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return
      updateUserFromSession(session)
    })

    return () => {
      mounted = false
      subscription?.unsubscribe()
    }
  }, [updateUserFromSession])

  const login = useCallback(async (email, password) => {
    const normalizedEmail = (email || '').trim().toLowerCase()
    const normalizedPassword = password || ''

    const { data, error } = await supabase.auth.signInWithPassword({
      email: normalizedEmail,
      password: normalizedPassword,
    })
    if (error) {
   
      if (error.message === 'Email not confirmed') {
        const { data: retryData, error: retryError } = await supabase.auth.signUp({
          email: normalizedEmail,
          password: normalizedPassword,
        })
        if (!retryError && retryData?.session) {
          return {
            access_token: retryData.session.access_token,
            user: { id: retryData.user.id, email: retryData.user.email ?? '' },
          }
        }
      }

      const message =
        error.message === 'Invalid login credentials'
          ? 'Invalid email or password. Please check and try again.'
          : error.message === 'Email not confirmed'
            ? 'Your email is not confirmed. Please sign up again or check your inbox.'
            : error.message || 'Sign in failed. Please try again.'
      const err = new Error(message)
      err.response = { data: { detail: message } }
      err.supabaseCode = error.code
      throw err
    }
    return {
      access_token: data.session.access_token,
      user: { id: data.user.id, email: data.user.email ?? '' },
    }
  }, [])

  const signup = useCallback(async (email, password) => {
    const normalizedEmail = (email || '').trim().toLowerCase()
    const normalizedPassword = password || ''

    const { data, error } = await supabase.auth.signUp({
      email: normalizedEmail,
      password: normalizedPassword,
    })
    if (error) {
      const err = new Error(error.message || 'Signup failed')
      err.response = { data: { detail: error.message } }
      throw err
    }

    // Supabase returns identities=[] when the email already exists (privacy).
    // Detect this and try signing in instead.
    if (data.user && data.user.identities && data.user.identities.length === 0) {
      // User already exists — attempt sign in directly
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
        email: normalizedEmail,
        password: normalizedPassword,
      })
      if (signInError) {
        const err = new Error(
          'An account with this email already exists. Please go to Sign In.'
        )
        err.response = { data: { detail: err.message } }
        throw err
      }
      return {
        access_token: signInData.session.access_token,
        user: { id: signInData.user.id, email: signInData.user.email ?? '' },
      }
    }

    // If Supabase returned a session, user is auto-confirmed (confirmation disabled)
    if (data.session) {
      return {
        access_token: data.session.access_token,
        user: { id: data.user.id, email: data.user.email ?? '' },
      }
    }

    // No session = email confirmation is required
    return {
      access_token: null,
      user: { id: data.user?.id, email: data.user?.email ?? '' },
      message: 'Check your email for the confirmation link, then sign in.',
    }
  }, [])

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) {
      const err = new Error(error.message || 'Google sign-in failed')
      err.response = { data: { detail: err.message } }
      throw err
    }
    // Browser will redirect to Google — no return value needed
  }, [])

  const resetPassword = useCallback(async (email) => {
    const normalizedEmail = (email || '').trim().toLowerCase()
    const { error } = await supabase.auth.resetPasswordForEmail(normalizedEmail, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    if (error) {
      const err = new Error(error.message || 'Failed to send reset email')
      err.response = { data: { detail: err.message } }
      throw err
    }
  }, [])

  const updatePassword = useCallback(async (newPassword) => {
    const { error } = await supabase.auth.updateUser({ password: newPassword })
    if (error) {
      const err = new Error(error.message || 'Failed to update password')
      err.response = { data: { detail: err.message } }
      throw err
    }
  }, [])

  const logout = useCallback(async () => {
    await supabase.auth.signOut()
    setToken(null)
    // Redirect to home page after sign out
    window.location.href = '/'
  }, [setToken])

  const value = {
    user,
    token,
    loading,
    login,
    signup,
    signInWithGoogle,
    resetPassword,
    updatePassword,
    logout,
    isAuthenticated: !!token,
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
