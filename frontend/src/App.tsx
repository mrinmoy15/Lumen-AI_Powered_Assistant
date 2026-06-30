import { useCallback, useEffect, useState } from 'react'
import type { Message, Thread } from './lib/types'
import { deleteThread, getMessages, getThreads, registerThread } from './lib/api'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'

function randomId() {
  return crypto.randomUUID()
}

export default function App() {
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string>(randomId)
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [docByThread, setDocByThread] = useState<Record<string, string>>({})

  // Load threads on mount
  useEffect(() => {
    getThreads().then(setThreads).catch(console.error)
  }, [])

  const switchThread = useCallback(async (threadId: string) => {
    setActiveThreadId(threadId)
    try {
      setMessages(await getMessages(threadId))
    } catch {
      setMessages([])
    }
  }, [])

  const newChat = useCallback(() => {
    setActiveThreadId(randomId())
    setMessages([])
  }, [])

  const handleDelete = useCallback(
    async (threadId: string) => {
      await deleteThread(threadId).catch(console.error)
      setThreads((prev) => prev.filter((t) => t.thread_id !== threadId))
      setDocByThread((prev) => { const n = { ...prev }; delete n[threadId]; return n })
      if (threadId === activeThreadId) newChat()
    },
    [activeThreadId, newChat],
  )

  const handleFirstMessage = useCallback((label: string) => {
    registerThread(activeThreadId).catch(console.error)
    setThreads((prev) => [{ thread_id: activeThreadId, label }, ...prev])
  }, [activeThreadId])

  const handleDocChange = useCallback((threadId: string, name: string | null) => {
    setDocByThread((prev) => {
      const next = { ...prev }
      if (name) next[threadId] = name
      else delete next[threadId]
      return next
    })
  }, [])

  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-primary">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={switchThread}
        onNewChat={newChat}
        onDeleteThread={handleDelete}
        docByThread={docByThread}
        onDocChange={handleDocChange}
      />
      <ChatArea
        threadId={activeThreadId}
        messages={messages}
        setMessages={setMessages}
        onFirstMessage={handleFirstMessage}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
      />
    </div>
  )
}
