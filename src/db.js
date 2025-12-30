import Dexie from 'dexie'

export const db = new Dexie('PeroperoChatDB')

db.version(3).stores({
  conversations: '++id, timestamp, source, session_id',
  settings: 'key',
  memories: '++id, *tags, importance, timestamp, msgTimestamp, type, source'
})

// Initialize default settings if not exists
export async function initLocalDB() {
  const count = await db.settings.where('key').equals('conversation_count').first()
  if (!count) {
    await db.settings.add({ key: 'conversation_count', value: 0 })
  }
}

export async function incrementConversationCount() {
  const item = await db.settings.where('key').equals('conversation_count').first()
  if (item) {
    const newVal = (item.value || 0) + 1
    await db.settings.update('conversation_count', { value: newVal })
    return newVal
  }
  return 0
}

export async function resetLocalDB() {
  await db.conversations.clear()
  await db.memories.clear()
  await db.settings.update('conversation_count', { value: 0 })
}
