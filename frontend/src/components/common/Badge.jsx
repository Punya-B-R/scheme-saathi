const colorMap = {
  blue: 'bg-blue-50 text-blue-700 border-blue-200/80 ring-blue-600/10',
  green: 'bg-emerald-50 text-emerald-700 border-emerald-200/80 ring-emerald-600/10',
  purple: 'bg-violet-50 text-violet-700 border-violet-200/80 ring-violet-600/10',
  orange: 'bg-orange-50 text-orange-700 border-orange-200/80 ring-orange-600/10',
  red: 'bg-red-50 text-red-700 border-red-200/80 ring-red-600/10',
  gray: 'bg-gray-100 text-gray-600 border-gray-200/80 ring-gray-600/10',
  indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200/80 ring-indigo-600/10',
}

export default function Badge({ children, color = 'blue', dot = false, className = '' }) {
  return (
    <span
      className={`
        inline-flex items-center gap-1
        px-2 py-0.5 rounded-md
        text-[11px] font-medium leading-5
        border ring-1
        ${colorMap[color] || colorMap.blue}
        ${className}
      `}
    >
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      )}
      {children}
    </span>
  )
}
