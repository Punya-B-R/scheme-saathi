import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Sparkles, Menu, LogIn, UserPlus, LogOut } from 'lucide-react'
import toast from 'react-hot-toast'
import { APP_NAME, QUICK_PROMPTS } from '../../utils/constants'
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
} from '../../services/storage'
import ChatSidebar from './ChatSidebar'
import ChatMessages from './ChatMessages'
import ChatInput from './ChatInput'

const QUICK_PROMPT_SET = new Set(QUICK_PROMPTS)

export default function ChatContainer() {
  const navigate = useNavigate()
  const { chatId: urlChatId } = useParams()
  const { isAuthenticated, user, logout, loading: authLoading } = useAuth()

  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChat] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendUp, setBackendUp] = useState(null)
  const [schemesCount, setSchemesCount] = useState(0)

  // Track the backend chat_id returned by /chat (for grouping messages in Supabase)
  const backendChatIdRef = useRef(null)

  // Health check on mount
  useEffect(() => {
    getHealthStatus()
      .then((d) => { setBackendUp(true); setSchemesCount(d.total_schemes || 0) })
      .catch(() => setBackendUp(false))
  }, [])

  // Load chats when auth state changes
  useEffect(() => {
    if (authLoading) return
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
        .catch((err) => {
          console.warn('Failed to load chats from backend:', err?.message)
          setChats([]) // Empty list, NOT localStorage (which is shared across users)
        })
    } else {
      setChats(getAllChats())
    }
  }, [isAuthenticated, authLoading])

  // Handle URL chat id
  useEffect(() => {
    if (!urlChatId) return
    if (isAuthenticated) {
      getBackendChat(urlChatId)
        .then((chat) => {
          setCurrentChat(String(chat.id))
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
        setCurrentChat(urlChatId)
        setMessages(chat.messages || [])
        setCurrentChatId(urlChatId)
      } else {
        navigate('/chat', { replace: true })
      }
    }
  }, [urlChatId, navigate, isAuthenticated])

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

  const handleNewChat = useCallback(() => {
    backendChatIdRef.current = null
    setCurrentChat(null)
    setMessages([])
    navigate('/chat', { replace: true })
  }, [navigate])

  const handleSelectChat = useCallback((id) => {
    if (isAuthenticated) {
      getBackendChat(id)
        .then((chat) => {
          setCurrentChat(String(chat.id))
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
        setCurrentChat(id)
        setMessages(chat.messages || [])
        setCurrentChatId(id)
        navigate(`/chat/${id}`, { replace: true })
      }
    }
  }, [navigate, isAuthenticated])

  const handleDeleteChat = useCallback((id) => {
    if (isAuthenticated) {
      deleteBackendChat(id)
        .then(() => {
          refreshChats()
          if (String(id) === String(currentChatId)) {
            backendChatIdRef.current = null
            setCurrentChat(null)
            setMessages([])
            navigate('/chat', { replace: true })
          }
        })
        .catch(() => toast.error('Failed to delete chat'))
    } else {
      deleteChat(id)
      refreshChats()
      if (id === currentChatId) {
        setCurrentChat(null)
        setMessages([])
        navigate('/chat', { replace: true })
      }
    }
  }, [currentChatId, navigate, refreshChats, isAuthenticated])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    // For non-authenticated users, use localStorage
    let activeChatId = currentChatId
    if (!isAuthenticated && !activeChatId) {
      const chat = createNewChat()
      activeChatId = chat.id
      setCurrentChat(chat.id)
      setCurrentChatId(chat.id)
      refreshChats()
      navigate(`/chat/${chat.id}`, { replace: true })
    }

    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    if (!isAuthenticated) {
      saveMessageToChat(activeChatId, userMsg)
    }
    setInput('')
    setLoading(true)

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      // Pass backend chat_id so messages group in the same chat in Supabase
      const data = await sendChatMessage(text, history, 'en', backendChatIdRef.current)

      // Store the backend chat_id for future messages in this conversation
      if (data.chat_id) {
        backendChatIdRef.current = data.chat_id
        if (!currentChatId) {
          setCurrentChat(String(data.chat_id))
          navigate(`/chat/${data.chat_id}`, { replace: true })
        }
      }

      const assistantMsg = {
        role: 'assistant',
        content: data.message,
        schemes: data.schemes || [],
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])

      if (!isAuthenticated) {
        saveMessageToChat(activeChatId, assistantMsg)
      }
      refreshChats()
    } catch {
      const errorMsg = {
        role: 'assistant',
        content: 'Sorry, I could not reach the server. Please make sure the backend is running on port 8000.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
      if (!isAuthenticated) {
        saveMessageToChat(activeChatId, errorMsg)
      }
      toast.error('Could not connect to server')
    } finally {
      setLoading(false)
    }
  }, [input, loading, currentChatId, messages, navigate, refreshChats, isAuthenticated])

  const handlePromptClick = useCallback((prompt) => {
    setInput(prompt)
    setTimeout(() => {
      setInput(prompt)
    }, 50)
  }, [])

  // Auto-send when input is set from prompt click
  useEffect(() => {
    if (input && !loading && QUICK_PROMPT_SET.has(input)) {
      handleSend()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [input])

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <ChatSidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="w-9 h-9 rounded-lg hover:bg-gray-100 flex items-center justify-center lg:hidden"
            >
              <Menu className="w-5 h-5 text-gray-500" />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-600 to-accent-purple flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-gray-900">{APP_NAME}</h1>
                <p className="text-[11px] text-gray-400">AI Scheme Finder</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
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
            {backendUp !== null && (
              <span className={`text-[11px] px-2.5 py-1 rounded-full font-medium ${
                backendUp
                  ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                  : 'bg-red-50 text-red-600 border border-red-200'
              }`}>
                {backendUp ? `${schemesCount.toLocaleString()} schemes` : 'Offline'}
              </span>
            )}
          </div>
        </header>

        {/* Messages */}
        <ChatMessages
          messages={messages}
          loading={loading}
          onPromptClick={(prompt) => {
            setInput(prompt)
          }}
        />

        {/* Input */}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          loading={loading}
        />
      </div>
    </div>
  )
}
