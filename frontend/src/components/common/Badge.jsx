const colors = {
  blue: 'bg-primary-50 text-primary-700 border-primary-200',
  green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  purple: 'bg-purple-50 text-purple-700 border-purple-200',
  orange: 'bg-orange-50 text-orange-700 border-orange-200',
  gray: 'bg-gray-100 text-gray-600 border-gray-200',
}

export default function Badge({ children, color = 'blue', className = '' }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[color]} ${className}`}>
      {children}
    </span>
  )
}
