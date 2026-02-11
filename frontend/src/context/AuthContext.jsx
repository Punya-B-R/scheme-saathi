import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { STORAGE_KEYS } from '../utils/constants'

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
          setUser(null)
          setToken(null)
          setLoading(false)
          return
        }
        if (session) updateUserFromSession(session)
      } catch (_) {
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
    const { data, error } = await supabase.auth.signInWithPassword({
      email: (email || '').trim().toLowerCase(),
      password: password || '',
    })
    if (error) {
      const message =
        error.message === 'Invalid login credentials'
          ? 'Invalid email or password. Please check and try again.'
          : error.message === 'Email not confirmed'
            ? 'Please confirm your email using the link we sent you, then try again.'
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
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) {
      const err = new Error(error.message || 'Signup failed')
      err.response = { data: { detail: error.message } }
      throw err
    }
    if (!data.session) {
      return {
        access_token: null,
        user: { id: data.user?.id, email: data.user?.email ?? '' },
        message: 'Check your email for the confirmation link.',
      }
    }
    return {
      access_token: data.session.access_token,
      user: { id: data.user.id, email: data.user.email ?? '' },
    }
  }, [])

  const logout = useCallback(async () => {
    await supabase.auth.signOut()
    setToken(null)
  }, [setToken])

  const value = {
    user,
    token,
    loading,
    login,
    signup,
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
