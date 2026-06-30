import { useRef, useState } from 'react'
import { Paperclip, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { uploadDocument, removeDocument } from '@/lib/api'

const SUPPORTED = ['.pdf', '.docx', '.doc', '.txt', '.csv', '.pptx']

interface Props {
  threadId: string
  loadedDoc: string | null
  onDocChange: (name: string | null) => void
}

export default function DocumentUpload({ threadId, loadedDoc, onDocChange }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!SUPPORTED.includes(ext)) {
      setErrorMsg(`Unsupported type: ${ext}. Supported: ${SUPPORTED.join(', ')}`)
      setStatus('error')
      return
    }
    setStatus('loading')
    setErrorMsg('')
    try {
      await uploadDocument(threadId, file)
      onDocChange(file.name)
      setStatus('idle')
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : String(e))
      setStatus('error')
    }
  }

  const handleRemove = async () => {
    await removeDocument(threadId).catch(() => {})
    onDocChange(null)
    setStatus('idle')
    setErrorMsg('')
  }

  if (loadedDoc) {
    return (
      <div className="mt-2">
        <div className="flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 px-3 py-2 text-xs text-accent-muted">
          <Paperclip className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1 truncate font-medium">{loadedDoc}</span>
          <button onClick={handleRemove} className="text-text-muted hover:text-red-400 transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-2">
      <input
        ref={fileRef}
        type="file"
        accept={SUPPORTED.join(',')}
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      <Button
        variant="outline"
        size="sm"
        className="w-full text-xs"
        disabled={status === 'loading'}
        onClick={() => fileRef.current?.click()}
      >
        {status === 'loading' ? (
          <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Processing...</>
        ) : (
          <><Paperclip className="h-3.5 w-3.5" /> Attach document</>
        )}
      </Button>
      {status === 'error' && (
        <p className="mt-1 text-[10px] text-red-400">{errorMsg}</p>
      )}
      <p className="mt-1 text-[10px] text-text-dim">{SUPPORTED.join(', ')}</p>
    </div>
  )
}
