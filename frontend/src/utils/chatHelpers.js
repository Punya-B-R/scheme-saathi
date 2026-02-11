/**
 * Group chats by date for sidebar display
 */
export function groupChatsByDate(chats) {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)

  const groups = { today: [], yesterday: [], week: [], older: [] }

  chats.forEach((chat) => {
    const date = new Date(chat.updatedAt || chat.createdAt)
    if (date >= today) groups.today.push(chat)
    else if (date >= yesterday) groups.yesterday.push(chat)
    else if (date >= weekAgo) groups.week.push(chat)
    else groups.older.push(chat)
  })

  return groups
}

export function getChatTitle(chat) {
  const title = chat?.title || 'New Conversation'
  return title.length > 30 ? title.substring(0, 30) + '…' : title
}
