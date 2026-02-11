import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, MessageSquare, Star } from 'lucide-react'

export default function CTA() {
  return (
    <section id="about" className="py-20 lg:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          className="relative max-w-3xl mx-auto rounded-3xl p-8 sm:p-12 lg:p-14 text-center overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0,0,0,0.05)',
          }}
        >
          <p className="text-xs font-semibold tracking-wider uppercase text-blue-600 mb-3">
            Get Started Today
          </p>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900">
            Start finding your schemes in 30 seconds
          </h2>
          <p className="mt-4 text-base sm:text-lg text-gray-600 max-w-xl mx-auto">
            No account needed. Just tell us about yourself and let AI do the rest.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/chat" className="btn-primary text-base px-8 py-3.5">
              <MessageSquare className="w-5 h-5" />
              Try Scheme Saathi Free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a href="#features" className="btn-ghost px-6 py-3">
              Learn More
            </a>
          </div>
          <p className="mt-8 text-sm text-gray-500">
            Trusted by thousands of Indians
          </p>
          <div className="mt-2 flex items-center justify-center gap-1 text-amber-500">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star key={i} className="w-4 h-4 fill-current" />
            ))}
            <span className="ml-2 text-sm text-gray-500">4.9/5</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
