import { useEffect, useRef, useState } from 'react'
import type { Message } from '@/lib/types'
import { streamChat } from '@/lib/api'
import WelcomeScreen from './WelcomeScreen'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'

interface Props {
  threadId: string
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  onFirstMessage: (label: string) => void
  isStreaming: boolean
  setIsStreaming: (v: boolean) => void
}

export default function ChatArea({ threadId, messages, setMessages, onFirstMessage, isStreaming, setIsStreaming }: Props) {
  const [input, setInput] = useState('')
  const [streamingText, setStreamingText] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')

    if (messages.length === 0) {
      onFirstMessage(text.slice(0, 40) + (text.length > 40 ? '...' : ''))
    }

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setStreamingText('')
    setIsStreaming(true)

    try {
      const full = await streamChat(threadId, text, setStreamingText)
      setMessages((prev) => [...prev, { role: 'assistant', content: full || 'No response received.' }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : String(err)}` },
      ])
    } finally {
      setStreamingText(null)
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && streamingText === null ? (
          <WelcomeScreen />
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {streamingText !== null && (
              <MessageBubble
                message={{ role: 'assistant', content: streamingText }}
                isStreaming
              />
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput value={input} onChange={setInput} onSend={handleSend} disabled={isStreaming} />
    </div>
  )
}
