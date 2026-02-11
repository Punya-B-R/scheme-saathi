export default function Card({ children, className = '', hover = false, glass = false }) {
  return (
    <div
      className={`rounded-2xl border ${glass ? 'glass' : 'bg-white border-gray-200'} ${hover ? 'card-hover' : ''} ${className}`}
    >
      {children}
    </div>
  )
}
