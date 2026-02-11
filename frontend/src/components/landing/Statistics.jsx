import { motion } from 'framer-motion'
import { STATISTICS } from '../../utils/constants'

export default function Statistics() {
  return (
    <section className="py-16 lg:py-20 bg-gradient-to-r from-primary-600 via-primary-700 to-accent-purple">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATISTICS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <p className="text-3xl sm:text-4xl font-extrabold text-white mb-1">{stat.value}</p>
              <p className="text-sm text-primary-100 font-medium">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
