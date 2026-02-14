import { createClient } from '@supabase/supabase-js'

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL || '').trim()
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY || '').trim()

const noop = () => {}
const noopAsync = async () => ({ data: { session: null }, error: null })
const noopSub = () => ({ data: { subscription: { unsubscribe: noop } } })

const stubAuth = {
  getSession: () => noopAsync(),
  onAuthStateChange: () => noopSub(),
  signOut: () => Promise.resolve(),
  signInWithPassword: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured' } }),
  signUp: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured' } }),
  signInWithOAuth: () => Promise.resolve({ error: { message: 'Supabase not configured' } }),
  resetPasswordForEmail: () => Promise.resolve({ error: { message: 'Supabase not configured' } }),
  updateUser: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured' } }),
}

let supabaseClient
try {
  supabaseClient = supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null
} catch (e) {
  console.warn('Supabase init failed:', e)
  supabaseClient = null
}

export const supabase = supabaseClient || { auth: stubAuth }
