export default function Card({
  children,
  className = '',
  hover = false,
  glass = false,
  padding = 'p-6',
  as: Component = 'div',
  ...props
}) {
  return (
    <Component
      className={`
        rounded-2xl border
        ${glass ? 'glass-card' : 'bg-white border-gray-200/80 shadow-sm'}
        ${hover ? 'card-lift cursor-pointer' : ''}
        ${padding}
        ${className}
      `}
      {...props}
    >
      {children}
    </Component>
  )
}
