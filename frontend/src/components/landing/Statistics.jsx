import { useState, useEffect, useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { STATISTICS } from '../../utils/constants'

function AnimatedStat({ value, label, delay = 0 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  const [display, setDisplay] = useState(value)

  const match = value.match(/^([^\d]*)(\d+)(.*)$/)
  const prefix = match ? match[1] : ''
  const numericPart = match ? match[2] : null
  const suffix = match ? match[3] : ''
  const isNumeric = numericPart != null

  useEffect(() => {
    if (!inView || !isNumeric) {
      setDisplay(value)
      return
    }
    const target = parseInt(numericPart, 10)
    const duration = 1500
    const start = Date.now()
    const timer = setInterval(() => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - (1 - progress) ** 2
      const current = Math.round(eased * target)
      setDisplay(prefix + current + suffix)
      if (progress >= 1) clearInterval(timer)
    }, 16)
    return () => clearInterval(timer)
  }, [inView, value, isNumeric, numericPart, prefix, suffix])

  return (
    <div ref={ref} className="text-center">
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay }}
        className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white"
      >
        {display}
      </motion.p>
      <motion.p
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: delay + 0.1 }}
        className="mt-1.5 text-sm font-medium text-blue-100"
      >
        {label}
      </motion.p>
    </div>
  )
}

export default function Statistics() {
  return (
    <section className="py-16 lg:py-24 gradient-blue-purple relative overflow-hidden">
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
        backgroundSize: '24px 24px',
      }} />
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          {STATISTICS.map((stat, i) => (
            <div key={stat.label} className={i < STATISTICS.length - 1 ? 'lg:border-r lg:border-blue-400/30' : ''}>
              <AnimatedStat value={stat.value} label={stat.label} delay={i * 0.08} />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
