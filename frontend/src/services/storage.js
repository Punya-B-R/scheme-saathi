import { STORAGE_KEYS } from '../utils/constants'

export const getAllChats = () => {
  try {
    const chats = localStorage.getItem(STORAGE_KEYS.CHATS)
    return chats ? JSON.parse(chats) : []
  } catch {
    return []
  }
}

export const getChatById = (chatId) => {
  return getAllChats().find((c) => c.id === chatId)
}

export const createNewChat = () => {
  const chat = {
    id: `chat_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    title: 'New Conversation',
    messages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
  const chats = getAllChats()
  chats.unshift(chat)
  saveChats(chats)
  return chat
}

export const saveMessageToChat = (chatId, message) => {
  const chats = getAllChats()
  const idx = chats.findIndex((c) => c.id === chatId)
  if (idx === -1) return

  // Save COMPLETE message object including schemes (don't strip fields)
  chats[idx].messages.push({
    ...message,
    schemes: Array.isArray(message.schemes) ? message.schemes : [],
  })
  chats[idx].updatedAt = new Date().toISOString()

  if (chats[idx].messages.filter((m) => m.role === 'user').length === 1 && message.role === 'user') {
    chats[idx].title = (message.content || '').length > 45 ? message.content.slice(0, 45) + '...' : (message.content || 'New Conversation')
  }
  saveChats(chats)
}

export const deleteChat = (chatId) => {
  saveChats(getAllChats().filter((c) => c.id !== chatId))
}

export const clearAllChats = () => {
  localStorage.removeItem(STORAGE_KEYS.CHATS)
}

export const getCurrentChatId = () => localStorage.getItem(STORAGE_KEYS.CURRENT_CHAT_ID)
export const setCurrentChatId = (id) => localStorage.setItem(STORAGE_KEYS.CURRENT_CHAT_ID, id)

const saveChats = (chats) => {
  try {
    localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(chats))
  } catch (e) {
    console.error('Storage save failed:', e)
  }
}
