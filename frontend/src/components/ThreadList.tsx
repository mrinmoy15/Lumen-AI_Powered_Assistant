import { Trash2 } from 'lucide-react'
import type { Thread } from '@/lib/types'
import { cn } from '@/lib/utils'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter, DialogClose,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

interface Props {
  threads: Thread[]
  activeThreadId: string
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export default function ThreadList({ threads, activeThreadId, onSelect, onDelete }: Props) {
  const [pendingDelete, setPendingDelete] = useState<Thread | null>(null)

  return (
    <>
      <div className="flex flex-col gap-1">
        {threads.map((t) => (
          <div key={t.thread_id} className="group flex items-center gap-1">
            <button
              onClick={() => onSelect(t.thread_id)}
              className={cn(
                'flex-1 truncate rounded-lg px-3 py-2 text-left text-sm transition-colors',
                t.thread_id === activeThreadId
                  ? 'bg-accent/20 text-accent-muted'
                  : 'text-text-muted hover:bg-white/5 hover:text-text-primary',
              )}
            >
              {t.label}
            </button>
            <button
              onClick={() => setPendingDelete(t)}
              className="shrink-0 rounded p-1 text-text-dim opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
              title="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>

      <Dialog open={!!pendingDelete} onOpenChange={(o) => !o && setPendingDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete conversation?</DialogTitle>
            <DialogDescription>
              "{pendingDelete?.label}" will be permanently removed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" size="sm">Cancel</Button>
            </DialogClose>
            <Button
              variant="danger"
              size="sm"
              onClick={() => {
                if (pendingDelete) onDelete(pendingDelete.thread_id)
                setPendingDelete(null)
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
