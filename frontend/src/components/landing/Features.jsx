import { motion } from 'framer-motion'
import { Brain, Database, CheckCircle, Globe } from 'lucide-react'
import { FEATURES } from '../../utils/constants'

const ICONS = { brain: Brain, database: Database, check: CheckCircle, globe: Globe }
const GRADIENTS = [
  'from-blue-500 to-blue-600',
  'from-violet-500 to-purple-600',
  'from-emerald-500 to-teal-600',
  'from-orange-500 to-amber-500',
]

export default function Features() {
  return (
    <section id="features" className="py-20 lg:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          className="text-xs font-semibold tracking-wider uppercase text-blue-600 mb-2"
        >
          Features
        </motion.p>
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          className="text-3xl sm:text-4xl font-bold text-gray-900"
        >
          Everything you need to claim your benefits
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          className="mt-3 text-lg text-gray-600 max-w-2xl"
        >
          Designed for every Indian, regardless of language, location, or literacy
        </motion.p>

        <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 gap-6">
          {FEATURES.map((feature, i) => {
            const Icon = ICONS[feature.icon] || Brain
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ delay: i * 0.1 }}
                className="card-hover p-6 lg:p-8"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${GRADIENTS[i]} flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6 text-white" strokeWidth={2} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">{feature.description}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
