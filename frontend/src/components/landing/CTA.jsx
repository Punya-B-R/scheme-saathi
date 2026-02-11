import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import Button from '../common/Button'

export default function CTA() {
  return (
    <section className="py-20 lg:py-28">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Ready to Find Your Schemes?
          </h2>
          <p className="text-lg text-gray-500 mb-8 max-w-xl mx-auto">
            Join thousands of citizens who have discovered schemes they never knew existed.
          </p>
          <Link to="/chat">
            <Button variant="gradient" size="xl">
              Start Your Free Search
              <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
