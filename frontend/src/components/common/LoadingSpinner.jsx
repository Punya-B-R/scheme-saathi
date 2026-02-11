import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ size = 20, className = '', label = 'Loading...' }) {
  return (
    <div className={`flex items-center justify-center gap-2 ${className}`} role="status">
      <Loader2 size={size} className="animate-spin text-primary-600" />
      {label && <span className="text-sm text-gray-500">{label}</span>}
      <span className="sr-only">{label}</span>
    </div>
  )
}
