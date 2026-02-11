import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Sparkles, Menu } from 'lucide-react'
import toast from 'react-hot-toast'
import { APP_NAME } from '../../utils/constants'
import { sendChatMessage, getHealthStatus } from '../../services/api'
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

export default function ChatContainer() {
  const navigate = useNavigate()
  const { chatId: urlChatId } = useParams()

  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChat] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendUp, setBackendUp] = useState(null)
  const [schemesCount, setSchemesCount] = useState(0)

  // Load chats on mount
  useEffect(() => {
    const saved = getAllChats()
    setChats(saved)

    // Health check
    getHealthStatus()
      .then((d) => { setBackendUp(true); setSchemesCount(d.total_schemes || 0) })
      .catch(() => setBackendUp(false))
  }, [])

  // Handle URL chat id
  useEffect(() => {
    if (urlChatId) {
      const chat = getChatById(urlChatId)
      if (chat) {
        setCurrentChat(urlChatId)
        setMessages(chat.messages || [])
        setCurrentChatId(urlChatId)
      } else {
        navigate('/chat', { replace: true })
      }
    }
  }, [urlChatId, navigate])

  const refreshChats = useCallback(() => {
    setChats(getAllChats())
  }, [])

  const handleNewChat = useCallback(() => {
    const chat = createNewChat()
    setCurrentChat(chat.id)
    setMessages([])
    setCurrentChatId(chat.id)
    refreshChats()
    navigate(`/chat/${chat.id}`, { replace: true })
  }, [navigate, refreshChats])

  const handleSelectChat = useCallback((id) => {
    const chat = getChatById(id)
    if (chat) {
      setCurrentChat(id)
      setMessages(chat.messages || [])
      setCurrentChatId(id)
      navigate(`/chat/${id}`, { replace: true })
    }
  }, [navigate])

  const handleDeleteChat = useCallback((id) => {
    deleteChat(id)
    refreshChats()
    if (id === currentChatId) {
      setCurrentChat(null)
      setMessages([])
      navigate('/chat', { replace: true })
    }
  }, [currentChatId, navigate, refreshChats])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    // Create chat if none exists
    let activeChatId = currentChatId
    if (!activeChatId) {
      const chat = createNewChat()
      activeChatId = chat.id
      setCurrentChat(chat.id)
      setCurrentChatId(chat.id)
      refreshChats()
      navigate(`/chat/${chat.id}`, { replace: true })
    }

    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    saveMessageToChat(activeChatId, userMsg)
    setInput('')
    setLoading(true)

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const data = await sendChatMessage(text, history)

      const assistantMsg = {
        role: 'assistant',
        content: data.message,
        schemes: data.schemes || [],
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      saveMessageToChat(activeChatId, assistantMsg)
      refreshChats()
    } catch {
      const errorMsg = {
        role: 'assistant',
        content: 'Sorry, I could not reach the server. Please make sure the backend is running on port 8000.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
      saveMessageToChat(activeChatId, errorMsg)
      toast.error('Could not connect to server')
    } finally {
      setLoading(false)
    }
  }, [input, loading, currentChatId, messages, navigate, refreshChats])

  const handlePromptClick = useCallback((prompt) => {
    setInput(prompt)
    // Auto send after a tick
    setTimeout(() => {
      const fakeEvent = { trim: () => prompt }
      // Set and send
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

// Quick prompt detection for auto-send
import { QUICK_PROMPTS } from '../../utils/constants'
const QUICK_PROMPT_SET = new Set(QUICK_PROMPTS)
