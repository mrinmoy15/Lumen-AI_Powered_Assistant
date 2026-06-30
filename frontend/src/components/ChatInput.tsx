import { useRef, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface Props {
  value: string
  onChange: (v: string) => void
  onSend: () => void
  disabled?: boolean
}

export default function ChatInput({ value, onChange, onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null)

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const handleInput = () => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  return (
    <div className="border-t border-border bg-sidebar px-4 py-3">
      <div className="flex items-end gap-2 rounded-xl border border-border bg-card px-3 py-2 focus-within:border-accent/50 transition-colors">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => { onChange(e.target.value); handleInput() }}
          onKeyDown={handleKey}
          placeholder="Type your message here..."
          disabled={disabled}
          className={cn(
            'flex-1 resize-none bg-transparent text-sm text-text-primary placeholder:text-text-dim outline-none leading-relaxed',
            'max-h-40 overflow-y-auto',
          )}
          style={{ height: 'auto', minHeight: '1.5rem' }}
        />
        <Button
          size="icon"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="shrink-0 mb-0.5"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
      <p className="mt-1 text-center text-[10px] text-text-dim">
        Shift+Enter for new line
      </p>
    </div>
  )
}
