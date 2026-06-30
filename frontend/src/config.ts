declare global {
  interface Window {
    __BACKEND_URL__: string
  }
}

// Priority: runtime injection (Docker) > build-time env (Vite) > localhost default
export const BACKEND_URL =
  (window.__BACKEND_URL__ && window.__BACKEND_URL__ !== '%%BACKEND_URL%%'
    ? window.__BACKEND_URL__
    : undefined) ??
  import.meta.env.VITE_BACKEND_URL ??
  'http://localhost:8000'
