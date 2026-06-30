import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0d0d1a',
        sidebar:    '#13131f',
        card:       '#1a1a2e',
        border:     '#2a2a3e',
        accent:     '#7c6af7',
        'accent-muted': '#a99ef7',
        'text-primary':  '#e8e8f0',
        'text-muted':    '#6b7280',
        'text-dim':      '#45455a',
      },
      fontFamily: {
        mono: ['"Space Mono"', 'monospace'],
        sans: ['"DM Sans"', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
