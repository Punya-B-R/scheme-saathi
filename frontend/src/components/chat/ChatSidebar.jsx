import { Plus, MessageSquare, Trash2, X } from 'lucide-react'

export default function ChatSidebar({ chats, currentChatId, onSelectChat, onNewChat, onDeleteChat, open, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 bg-black/30 z-40 lg:hidden" onClick={onClose} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:relative top-0 left-0 h-full w-72 bg-gray-50 border-r border-gray-200 z-50 lg:z-auto flex flex-col transition-transform duration-200 ${
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-700">Conversations</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={onNewChat}
              className="w-8 h-8 rounded-lg hover:bg-gray-200 flex items-center justify-center transition-colors text-gray-500 hover:text-gray-700"
              title="New chat"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg hover:bg-gray-200 flex items-center justify-center transition-colors text-gray-500 hover:text-gray-700 lg:hidden"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
          {chats.length === 0 ? (
            <p className="text-xs text-gray-400 text-center mt-8 px-4">
              No conversations yet. Start a new chat!
            </p>
          ) : (
            <div className="space-y-0.5">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                    chat.id === currentChatId
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => { onSelectChat(chat.id); onClose() }}
                >
                  <MessageSquare className="w-4 h-4 flex-shrink-0 opacity-50" />
                  <span className="text-sm truncate flex-1">{chat.title}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id) }}
                    className="w-6 h-6 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
