import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Menu, Plus, Home, Volume2, VolumeX, LogIn, UserPlus, LogOut } from 'lucide-react'
import toast from 'react-hot-toast'
import { APP_NAME } from '../../utils/constants'
import { useAuth } from '../../context/AuthContext'
import {
  sendChatMessage,
  getHealthStatus,
  listBackendChats,
  getBackendChat,
  deleteBackendChat,
} from '../../services/api'
import {
  getAllChats,
  getChatById,
  createNewChat,
  saveMessageToChat,
  deleteChat,
  setCurrentChatId,
  getCurrentChatId,
} from '../../services/storage'
import ChatSidebar from './ChatSidebar'
import ChatMessages from './ChatMessages'
import ChatInput from './ChatInput'
import { getChatTitle } from '../../utils/chatHelpers'
import LanguageToggle from './LanguageToggle'
import { useTranslation } from '../../utils/i18n'
import SpeakingIndicator from './SpeakingIndicator'

export default function ChatContainer() {
  const navigate = useNavigate()
  const { chatId: urlChatId } = useParams()
  const { isAuthenticated, user, logout, loading: authLoading } = useAuth()

  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatIdState] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendOk, setBackendOk] = useState(null)
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [language, setLanguage] = useState(
    () => localStorage.getItem('scheme_saathi_language') || 'en'
  )
  const voiceRef = useRef(null)
  const t = useTranslation(language)

  // Track the backend chat_id returned by /chat (for grouping messages in Supabase)
  const backendChatIdRef = useRef(null)

  const refreshChats = useCallback(() => {
    if (isAuthenticated) {
      listBackendChats()
        .then((backendChats) => {
          const mapped = (backendChats || []).map((c) => ({
            id: String(c.id),
            title: c.title || 'New Conversation',
            messages: [],
            createdAt: c.created_at,
            updatedAt: c.updated_at,
            isBackend: true,
          }))
          setChats(mapped)
        })
        .catch(() => setChats([]))
    } else {
      setChats(getAllChats())
    }
  }, [isAuthenticated])

  // Health check on mount
  useEffect(() => {
    getHealthStatus()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  // Load chats when auth state changes
  useEffect(() => {
    if (authLoading) return
    refreshChats()
  }, [isAuthenticated, authLoading, refreshChats])

  // Handle URL chat id
  useEffect(() => {
    if (urlChatId) {
      if (isAuthenticated) {
        getBackendChat(urlChatId)
          .then((chat) => {
            setCurrentChatIdState(String(chat.id))
            backendChatIdRef.current = chat.id
            setMessages(
              (chat.messages || []).map((m) => ({
                role: m.role,
                content: m.content,
                timestamp: m.timestamp,
              }))
            )
          })
          .catch(() => navigate('/chat', { replace: true }))
      } else {
        const chat = getChatById(urlChatId)
        if (chat) {
          setCurrentChatIdState(urlChatId)
          setCurrentChatId(urlChatId)
          setMessages(chat.messages || [])
        } else {
          navigate('/chat', { replace: true })
        }
      }
    } else {
      if (!isAuthenticated) {
        const saved = getCurrentChatId()
        const chat = saved ? getChatById(saved) : null
        if (chat) {
          setCurrentChatIdState(chat.id)
          setMessages(chat.messages || [])
        } else {
          setCurrentChatIdState(null)
          setMessages([])
        }
      } else {
        setCurrentChatIdState(null)
        setMessages([])
      }
    }
  }, [urlChatId, navigate, isAuthenticated])

  const handleNewChat = useCallback(() => {
    backendChatIdRef.current = null
    if (isAuthenticated) {
      setCurrentChatIdState(null)
      setMessages([])
      navigate('/chat', { replace: true })
    } else {
      const chat = createNewChat()
      setCurrentChatIdState(chat.id)
      setCurrentChatId(chat.id)
      setMessages([])
      refreshChats()
      navigate(`/chat/${chat.id}`, { replace: true })
    }
    setSidebarOpen(false)
  }, [navigate, refreshChats, isAuthenticated])

  const handleSelectChat = useCallback((id) => {
    if (isAuthenticated) {
      getBackendChat(id)
        .then((chat) => {
          setCurrentChatIdState(String(chat.id))
          backendChatIdRef.current = chat.id
          setMessages(
            (chat.messages || []).map((m) => ({
              role: m.role,
              content: m.content,
              timestamp: m.timestamp,
            }))
          )
          navigate(`/chat/${chat.id}`, { replace: true })
        })
        .catch(() => {})
    } else {
      const chat = getChatById(id)
      if (chat) {
        setCurrentChatIdState(id)
        setCurrentChatId(id)
        setMessages(chat.messages || [])
        navigate(`/chat/${id}`, { replace: true })
      }
    }
    setSidebarOpen(false)
  }, [navigate, isAuthenticated])

  const handleDeleteChat = useCallback((id) => {
    if (isAuthenticated) {
      deleteBackendChat(id)
        .then(() => {
          refreshChats()
          if (String(id) === String(currentChatId)) {
            backendChatIdRef.current = null
            setCurrentChatIdState(null)
            setMessages([])
            navigate('/chat', { replace: true })
          }
        })
        .catch(() => toast.error('Failed to delete chat'))
    } else {
      deleteChat(id)
      refreshChats()
      if (id === currentChatId) {
        handleNewChat()
      }
    }
  }, [currentChatId, navigate, refreshChats, isAuthenticated, handleNewChat])

  const handleLanguageChange = useCallback((lang) => {
    setLanguage(lang)
    localStorage.setItem('scheme_saathi_language', lang)
  }, [])

  const handleVoiceReady = useCallback((controls) => {
    voiceRef.current = controls
    setIsSpeaking(!!controls?.isSpeaking)
  }, [])

  const handleSendMessage = useCallback(async (content, options = {}) => {
    const { fromVoice = false } = options || {}
    const text = (content || '').trim()
    if (!text || isLoading) return

    let chatId = currentChatId
    // For non-authenticated users, create a local chat if needed
    if (!isAuthenticated && !chatId) {
      const chat = createNewChat()
      chatId = chat.id
      setCurrentChatIdState(chatId)
      setCurrentChatId(chatId)
      refreshChats()
      navigate(`/chat/${chatId}`, { replace: true })
    }

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])
    if (!isAuthenticated && chatId) {
      saveMessageToChat(chatId, userMessage)
    }
    refreshChats()
    setIsLoading(true)

    try {
      const history = messages
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))
      const response = await sendChatMessage(text, history, null, language, backendChatIdRef.current)

      // Store the backend chat_id for future messages in this conversation
      if (response.chat_id) {
        backendChatIdRef.current = response.chat_id
        if (!currentChatId) {
          setCurrentChatIdState(String(response.chat_id))
          navigate(`/chat/${response.chat_id}`, { replace: true })
        }
      }

      const aiMessage = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: response.message || '',
        schemes: response.schemes || [],
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, aiMessage])
      if (!isAuthenticated && chatId) {
        saveMessageToChat(chatId, aiMessage)
      }
      refreshChats()

      // Always speak back for voice-originated messages.
      // For typed messages, follow the voice toggle.
      if ((fromVoice || voiceEnabled) && voiceRef.current?.speak) {
        setTimeout(() => {
          voiceRef.current?.speak(response.message || '')
        }, 500)
      }
    } catch {
      const errorMsg = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: t.errorMessage,
        schemes: [],
        isError: true,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
      if (!isAuthenticated && chatId) {
        saveMessageToChat(chatId, errorMsg)
      }
      refreshChats()
      toast.error(t.connectionError)
    } finally {
      setIsLoading(false)
    }
  }, [currentChatId, isLoading, messages, navigate, refreshChats, language, t.connectionError, t.errorMessage, voiceEnabled, isAuthenticated])

  const handleSuggestionClick = useCallback((text) => {
    handleSendMessage(text)
  }, [handleSendMessage])

  const handleSpeakMessage = useCallback((text) => {
    if (!text || !voiceRef.current?.speak) return
    voiceRef.current.speak(text)
  }, [])

  const currentChat = currentChatId ? getChatById(currentChatId) : null
  const headerTitle = currentChat ? getChatTitle(currentChat) : 'New Conversation'

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <ChatSidebar
        chats={chats}
        currentChatId={currentChatId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        language={language}
      />

      <div className="flex-1 flex flex-col min-w-0 relative">
        <SpeakingIndicator
          isSpeaking={isSpeaking}
          onStop={() => voiceRef.current?.stopSpeaking?.()}
        />
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-4 border-b border-gray-200 bg-white flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-sm font-semibold text-gray-900 truncate max-w-[200px] sm:max-w-xs">
              {headerTitle}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <LanguageToggle
              language={language}
              onLanguageChange={handleLanguageChange}
            />
            {!authLoading && (
              isAuthenticated ? (
                <>
                  <span className="hidden sm:inline text-xs text-gray-500 truncate max-w-[100px]" title={user?.email}>{user?.email}</span>
                  <button
                    type="button"
                    onClick={() => logout()}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1.5 rounded-lg hover:bg-gray-100"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1.5 rounded-lg hover:bg-gray-100">
                    <LogIn className="w-3.5 h-3.5" />
                    Log in
                  </Link>
                  <Link to="/signup" className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium px-2 py-1.5 rounded-lg hover:bg-primary-50">
                    <UserPlus className="w-3.5 h-3.5" />
                    Sign up
                  </Link>
                </>
              )
            )}
            {backendOk !== null && (
              <span
                className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                  backendOk ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'
                }`}
              >
                {backendOk ? 'Online' : 'Offline'}
              </span>
            )}
            <button
              type="button"
              onClick={() => setVoiceEnabled((v) => !v)}
              className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${
                voiceEnabled ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-gray-100'
              }`}
              title={voiceEnabled ? 'Disable voice' : 'Enable voice response'}
              aria-label={voiceEnabled ? 'Disable voice' : 'Enable voice response'}
            >
              {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
            <button
              type="button"
              onClick={handleNewChat}
              className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100"
              aria-label="New chat"
            >
              <Plus className="w-4 h-4" />
            </button>
            <Link
              to="/"
              className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100"
              aria-label="Back to home"
            >
              <Home className="w-4 h-4" />
            </Link>
          </div>
        </header>

        <ChatMessages
          messages={messages}
          isLoading={isLoading}
          onSuggestionClick={handleSuggestionClick}
          language={language}
          onSpeakMessage={handleSpeakMessage}
          isSpeaking={isSpeaking}
        />

        <ChatInput
          onSend={handleSendMessage}
          isLoading={isLoading}
          disabled={false}
          language={language}
          onVoiceReady={handleVoiceReady}
        />
      </div>
    </div>
  )
}
