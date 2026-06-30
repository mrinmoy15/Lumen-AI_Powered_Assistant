const cards = [
  {
    icon: '🔍',
    title: 'Web Search',
    desc: 'Search the web in real time for up-to-date news and information.',
  },
  {
    icon: '📈',
    title: 'Stock Prices',
    desc: 'Look up live stock prices and market data for any ticker symbol.',
  },
  {
    icon: '📄',
    title: 'Document Chat',
    desc: 'Upload a document (PDF, DOCX, TXT, CSV, PPTX) and ask questions about its contents.',
  },
]

export default function WelcomeScreen() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 pb-8">
      <div className="text-6xl" style={{ filter: 'drop-shadow(0 0 20px rgba(124,106,247,0.5))' }}>
        💡
      </div>
      <h1 className="font-mono text-5xl font-bold tracking-widest"
        style={{ background: 'linear-gradient(135deg,#a99ef7,#7c6af7,#5a4fd4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
        LUMEN
      </h1>
      <p className="font-sans text-sm font-light tracking-widest text-text-dim italic">
        - your helpful assistant -
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3 max-w-2xl">
        {cards.map((c) => (
          <div key={c.title} className="w-48 rounded-xl border border-accent/20 bg-accent/[0.08] p-4 text-left">
            <div className="mb-1.5 text-2xl">{c.icon}</div>
            <div className="mb-1 text-sm font-semibold text-accent-muted">{c.title}</div>
            <div className="text-xs leading-relaxed text-text-dim">{c.desc}</div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs tracking-widest text-text-dim">
        Type a message below to begin
      </p>
    </div>
  )
}
