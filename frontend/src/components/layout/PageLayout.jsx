import Navbar from './Navbar'

export default function PageLayout({ children, showNav = true }) {
  return (
    <div className="min-h-screen">
      {showNav && <Navbar />}
      {children}
    </div>
  )
}
