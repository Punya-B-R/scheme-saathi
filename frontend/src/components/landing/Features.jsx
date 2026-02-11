import { motion } from 'framer-motion'
import { Bot, Database, CheckCircle, Globe } from 'lucide-react'
import { FEATURES } from '../../utils/constants'
import Card from '../common/Card'

const iconMap = {
  bot: Bot,
  database: Database,
  check: CheckCircle,
  globe: Globe,
}

const colors = [
  'from-primary-500 to-primary-600',
  'from-accent-purple to-purple-600',
  'from-emerald-500 to-emerald-600',
  'from-accent-orange to-orange-600',
]

export default function Features() {
  return (
    <section id="features" className="py-20 lg:py-28 bg-gray-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Everything You Need
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Powered by AI and backed by official government data
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((feature, i) => {
            const Icon = iconMap[feature.icon] || Bot
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <Card hover className="p-6 h-full">
                  <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${colors[i]} flex items-center justify-center mb-4 shadow-lg`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
                </Card>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
