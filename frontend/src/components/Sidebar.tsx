import { Plus } from 'lucide-react'
import type { Thread } from '@/lib/types'
import { Button } from '@/components/ui/button'
import ThreadList from './ThreadList'
import DocumentUpload from './DocumentUpload'

interface Props {
  threads: Thread[]
  activeThreadId: string
  onSelectThread: (id: string) => void
  onNewChat: () => void
  onDeleteThread: (id: string) => void
  docByThread: Record<string, string>
  onDocChange: (threadId: string, name: string | null) => void
}

export default function Sidebar({
  threads, activeThreadId, onSelectThread, onNewChat, onDeleteThread, docByThread, onDocChange,
}: Props) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-sidebar">
      {/* Header */}
      <div className="border-b border-border px-4 py-4">
        <h1 className="font-mono text-sm font-bold tracking-widest text-accent-muted uppercase">
          Chatbot Powered by LangGraph
        </h1>
      </div>

      {/* New chat */}
      <div className="px-3 pt-3">
        <Button onClick={onNewChat} className="w-full" size="sm">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Document upload */}
      <div className="border-t border-border mt-3 px-3 pt-3">
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-text-dim">
          Document
        </p>
        <DocumentUpload
          threadId={activeThreadId}
          loadedDoc={docByThread[activeThreadId] ?? null}
          onDocChange={(name) => onDocChange(activeThreadId, name)}
        />
      </div>

      {/* Conversation list */}
      {threads.length > 0 && (
        <div className="mt-3 border-t border-border px-3 pt-3 flex-1 overflow-y-auto">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-text-dim">
            My Conversations
          </p>
          <ThreadList
            threads={threads}
            activeThreadId={activeThreadId}
            onSelect={onSelectThread}
            onDelete={onDeleteThread}
          />
        </div>
      )}
    </aside>
  )
}
