import Navbar from '../components/layout/Navbar'
import Hero from '../components/landing/Hero'
import Statistics from '../components/landing/Statistics'
import Features from '../components/landing/Features'
import HowItWorks from '../components/landing/HowItWorks'
import CTA from '../components/landing/CTA'
import Footer from '../components/layout/Footer'

export default function HomePage() {
  return (
    <>
      <Navbar />
      <Hero />
      <Statistics />
      <Features />
      <HowItWorks />
      <CTA />
      <Footer />
    </>
  )
}
