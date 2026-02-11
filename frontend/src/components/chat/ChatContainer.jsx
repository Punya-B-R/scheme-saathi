import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Menu, Plus, Home } from 'lucide-react'
import { Link } from 'react-router-dom'
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
  getCurrentChatId,
} from '../../services/storage'
import ChatSidebar from './ChatSidebar'
import ChatMessages from './ChatMessages'
import ChatInput from './ChatInput'
import { getChatTitle } from '../../utils/chatHelpers'

const ERROR_MESSAGE = 'Sorry, I encountered an error. Please check if the backend server is running and try again.'

export default function ChatContainer() {
  const navigate = useNavigate()
  const { chatId: urlChatId } = useParams()

  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatIdState] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [backendOk, setBackendOk] = useState(null)

  const refreshChats = useCallback(() => setChats(getAllChats()), [])

  useEffect(() => {
    refreshChats()
    getHealthStatus().then(() => setBackendOk(true)).catch(() => setBackendOk(false))
  }, [refreshChats])

  useEffect(() => {
    if (urlChatId) {
      const chat = getChatById(urlChatId)
      if (chat) {
        setCurrentChatIdState(urlChatId)
        setCurrentChatId(urlChatId)
        setMessages(chat.messages || [])
      } else {
        navigate('/chat', { replace: true })
      }
    } else {
      const saved = getCurrentChatId()
      const chat = saved ? getChatById(saved) : null
      if (chat) {
        setCurrentChatIdState(chat.id)
        setMessages(chat.messages || [])
      } else {
        setCurrentChatIdState(null)
        setMessages([])
      }
    }
  }, [urlChatId, navigate])

  const handleNewChat = useCallback(() => {
    const chat = createNewChat()
    setCurrentChatIdState(chat.id)
    setCurrentChatId(chat.id)
    setMessages([])
    refreshChats()
    navigate(`/chat/${chat.id}`, { replace: true })
    setSidebarOpen(false)
  }, [navigate, refreshChats])

  const handleSelectChat = useCallback((id) => {
    const chat = getChatById(id)
    if (chat) {
      setCurrentChatIdState(id)
      setCurrentChatId(id)
      setMessages(chat.messages || [])
      navigate(`/chat/${id}`, { replace: true })
      setSidebarOpen(false)
    }
  }, [navigate])

  const handleDeleteChat = useCallback((id) => {
    deleteChat(id)
    refreshChats()
    if (id === currentChatId) {
      handleNewChat()
    }
  }, [currentChatId, refreshChats, handleNewChat])

  const handleSendMessage = useCallback(async (content) => {
    const text = (content || '').trim()
    if (!text || isLoading) return

    let chatId = currentChatId
    if (!chatId) {
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
    saveMessageToChat(chatId, userMessage)
    refreshChats()
    setIsLoading(true)

    try {
      const history = messages
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))
      const response = await sendChatMessage(text, history)

      const aiMessage = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: response.message || '',
        schemes: response.schemes || [],
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, aiMessage])
      saveMessageToChat(chatId, aiMessage)
      refreshChats()
    } catch {
      const errorMsg = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: ERROR_MESSAGE,
        schemes: [],
        isError: true,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
      saveMessageToChat(chatId, errorMsg)
      refreshChats()
      toast.error('Could not reach the server')
    } finally {
      setIsLoading(false)
    }
  }, [currentChatId, isLoading, messages, navigate, refreshChats])

  const handleSuggestionClick = useCallback((text) => {
    handleSendMessage(text)
  }, [handleSendMessage])

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
      />

      <div className="flex-1 flex flex-col min-w-0">
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
        />

        <ChatInput
          onSend={handleSendMessage}
          isLoading={isLoading}
          disabled={false}
        />
      </div>
    </div>
  )
}
