import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, MessageSquare } from 'lucide-react'

const SUBHEAD = `Stop missing out on benefits you deserve.
Our AI has a simple conversation with you
and finds every scheme you're eligible for —
in seconds.`

export default function Hero() {
  return (
    <section id="home" className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background blobs */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-blue-400/20 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/3" />
      <div className="absolute top-0 left-0 w-[600px] h-[600px] bg-purple-400/20 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/3" />
      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28 w-full">
        <div className="max-w-4xl">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-blue-200/80 bg-blue-50/80 text-blue-700 text-sm font-medium mb-8"
          >
            <span>✨</span>
            Now with 850+ Government Schemes
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] text-gray-900"
          >
            Find Government Schemes
            <br />
            <span className="gradient-text">Made For You</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.16 }}
            className="mt-6 text-lg sm:text-xl text-gray-500 leading-relaxed whitespace-pre-line max-w-2xl"
          >
            {SUBHEAD}
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.24 }}
            className="mt-10 flex flex-col sm:flex-row items-start gap-3"
          >
            <Link to="/chat" className="btn-primary">
              <MessageSquare className="w-5 h-5" />
              Start Discovering Schemes
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a href="#how-it-works" className="btn-secondary">
              See How It Works
            </a>
          </motion.div>

          {/* Trust */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-8 text-sm text-gray-400"
          >
            ✓ Free forever &nbsp; ✓ Try it out now! &nbsp; ✓ 850+ schemes
          </motion.p>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-2 text-sm text-gray-500"
          >
            New here?{' '}
            <Link to="/signup" className="text-primary-600 font-medium hover:underline">Sign up</Link>
            {' or '}
            <Link to="/login" className="text-primary-600 font-medium hover:underline">Log in</Link>
            {' to get started.'}
          </motion.p>
        </div>

        {/* Chat mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mt-16 lg:mt-24 max-w-2xl mx-auto"
        >
          <div className="animate-float rounded-2xl border border-gray-200 bg-white shadow-2xl shadow-gray-200/50 p-6 noise">
            <div className="space-y-4">
              <div className="flex justify-end">
                <div className="message-bubble-user max-w-[85%]">
                  I'm a farmer in Bihar with 2 acres
                </div>
              </div>
              <div className="flex justify-start">
                <div className="message-bubble-ai">
                  <p className="font-medium text-gray-900 mb-2">Here are schemes that match:</p>
                  <div className="space-y-2">
                    <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-3 text-sm">
                      <p className="font-semibold text-gray-800">PM-KISAN</p>
                      <p className="text-gray-500 text-xs">₹6,000/year • All India</p>
                    </div>
                    <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-3 text-sm">
                      <p className="font-semibold text-gray-800">PM Fasal Bima Yojana</p>
                      <p className="text-gray-500 text-xs">Crop insurance • Bihar</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
