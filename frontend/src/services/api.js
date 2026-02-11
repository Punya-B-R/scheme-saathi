import axios from 'axios'
import { API_BASE_URL } from '../utils/constants'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    console.error('[API]', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

export async function sendChatMessage(message, conversationHistory = [], language = 'en') {
  const { data } = await api.post('/chat', {
    message,
    conversation_history: conversationHistory,
    language,
  })
  return data
}

export async function getHealthStatus() {
  const { data } = await api.get('/health')
  return data
}

export async function listSchemes(params = {}) {
  const { data } = await api.get('/schemes', { params })
  return data
}

export async function getSchemeById(schemeId) {
  const { data } = await api.get(`/schemes/${encodeURIComponent(schemeId)}`)
  return data
}

export async function searchSchemes(query, userContext = {}) {
  const { data } = await api.post('/search', { query, user_context: userContext })
  return data
}

export default api
