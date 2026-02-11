import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MessageCircle, Zap, ArrowRight } from 'lucide-react'
const STEPS_CONFIG = [
  {
    title: 'Start a Conversation',
    desc: 'Tell us about yourself - occupation, state, and what you need',
    icon: MessageCircle,
  },
  {
    title: 'Get Matched',
    desc: 'AI finds all schemes you qualify for instantly',
    icon: Zap,
  },
  {
    title: 'Apply with Confidence',
    desc: 'Get documents list, deadlines, and step-by-step guidance',
    icon: ArrowRight,
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 lg:py-32 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-xs font-semibold tracking-wider uppercase text-blue-600 mb-2"
        >
          How It Works
        </motion.p>
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-3xl sm:text-4xl font-bold text-gray-900"
        >
          Three steps to your benefits
        </motion.h2>

        <div className="mt-16 relative">
          {/* Connecting line (desktop) */}
          <div className="hidden lg:block absolute top-12 left-[16.67%] right-[16.67%] h-0.5 border-t-2 border-dashed border-gray-200" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-8">
            {STEPS_CONFIG.map((step, i) => {
              const Icon = step.icon
              const num = String(i + 1).padStart(2, '0')
              return (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.12 }}
                  className="relative text-center"
                >
                  <div className="inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-white border border-gray-100 shadow-sm mb-5 relative z-10">
                    <Icon className="w-10 h-10 text-blue-600" strokeWidth={1.8} />
                  </div>
                  <p className="text-2xl font-bold gradient-text-blue mb-2">{num}</p>
                  <h3 className="text-lg font-bold text-gray-900">{step.title}</h3>
                  <p className="mt-2 text-sm text-gray-500 leading-relaxed max-w-xs mx-auto">{step.desc}</p>
                </motion.div>
              )
            })}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-16 text-center"
          >
            <p className="text-gray-600 font-medium mb-4">Ready to discover your schemes?</p>
            <Link to="/chat" className="btn-primary">
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
