import PageLayout from '../components/layout/PageLayout'
import Hero from '../components/landing/Hero'
import Features from '../components/landing/Features'
import HowItWorks from '../components/landing/HowItWorks'
import Statistics from '../components/landing/Statistics'
import CTA from '../components/landing/CTA'
import Footer from '../components/landing/Footer'

export default function HomePage() {
  return (
    <PageLayout>
      <Hero />
      <Features />
      <Statistics />
      <HowItWorks />
      <CTA />
      <Footer />
    </PageLayout>
  )
}
