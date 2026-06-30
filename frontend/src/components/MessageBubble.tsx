import ReactMarkdown from 'react-markdown'
import type { Message } from '@/lib/types'
import { cn } from '@/lib/utils'

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3 px-2 py-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-lg">
          🤖
        </div>
      )}

      <div
        className={cn(
          'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-accent/80 text-white rounded-tr-sm'
            : 'bg-card border border-border text-text-primary rounded-tl-sm',
        )}
      >
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              code: ({ children }) => (
                <code className="rounded bg-white/10 px-1 py-0.5 font-mono text-xs">{children}</code>
              ),
              pre: ({ children }) => (
                <pre className="mb-2 overflow-x-auto rounded-lg bg-black/30 p-3 font-mono text-xs">{children}</pre>
              ),
              ul: ({ children }) => <ul className="mb-2 list-disc pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="mb-2 list-decimal pl-5">{children}</ol>,
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
        {isStreaming && (
          <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-accent-muted align-middle" />
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-lg">
          🧑
        </div>
      )}
    </div>
  )
}
