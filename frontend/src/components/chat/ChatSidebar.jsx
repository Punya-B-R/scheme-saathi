import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MessageSquare, ArrowLeft, X } from 'lucide-react'
import { APP_NAME } from '../../utils/constants'
import { groupChatsByDate, getChatTitle } from '../../utils/chatHelpers'

export default function ChatSidebar({
  chats = [],
  currentChatId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  isOpen,
  onClose,
}) {
  const groups = groupChatsByDate(chats)

  const handleDelete = (e, chatId) => {
    e.stopPropagation()
    if (window.confirm('Delete this conversation?')) {
      onDeleteChat(chatId)
    }
  }

  const renderGroup = (label, list) => {
    if (!list?.length) return null
    return (
      <div className="mb-4">
        <p className="px-3 mb-2 text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
          {label}
        </p>
        <div className="space-y-0.5">
          {list.map((chat) => (
            <div
              key={chat.id}
              onClick={() => onSelectChat(chat.id)}
              className="group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors"
              style={{
                backgroundColor: chat.id === currentChatId ? 'rgba(55, 65, 81, 1)' : 'transparent',
              }}
            >
              <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="flex-1 text-sm text-gray-200 truncate">{getChatTitle(chat)}</span>
              <button
                type="button"
                onClick={(e) => handleDelete(e, chat.id)}
                className="w-6 h-6 rounded flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-600 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                aria-label="Delete chat"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const sidebarContent = (
    <div className="flex flex-col h-full w-[260px] bg-gray-900 flex-shrink-0">
      {/* Top: Logo + New Chat */}
      <div className="p-3 border-b border-gray-700/80">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-blue-500 to-violet-500 flex items-center justify-center">
              <span className="text-white font-bold text-xs">SS</span>
            </div>
            <span className="text-white font-semibold text-[15px]">{APP_NAME}</span>
          </div>
          {isOpen != null && (
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-700 hover:text-white"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-700/80 hover:text-white transition-colors text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-2">
        {chats.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <MessageSquare className="w-12 h-12 text-gray-600 mb-3" />
            <p className="text-sm text-gray-500 mb-1">No conversations yet</p>
            <button
              type="button"
              onClick={onNewChat}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Start a new chat →
            </button>
          </div>
        ) : (
          <>
            {renderGroup('Today', groups.today)}
            {renderGroup('Yesterday', groups.yesterday)}
            {renderGroup('Previous 7 Days', groups.week)}
            {renderGroup('Older', groups.older)}
          </>
        )}
      </div>

      {/* Bottom */}
      <div className="p-3 border-t border-gray-700/80 space-y-2">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
        <p className="text-[11px] text-gray-500">{APP_NAME} v1.0</p>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      {/* Sidebar: slide in on mobile, static on desktop */}
      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
          transform transition-transform duration-200 ease-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {sidebarContent}
      </aside>
    </>
  )
}
