import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '../lib/auth'

export default function Navigation() {
  const { isAuthenticated, signOut } = useAuth()
  const router = useRouter()
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleLogout = async () => {
    try {
      await signOut()
      window.location.href = '/'
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  const isActive = (path: string) => router.pathname === path

  return (
    <>
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        background: 'var(--skeuo-bg)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.4)',
        boxShadow: scrolled ? '0 10px 20px rgba(0,0,0,0.1)' : '0 4px 10px rgba(0,0,0,0.05)',
        padding: '0.8rem 0',
        transition: 'all 0.3s ease'
      }}>
        <div className="container flex justify-between items-center" style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 1.5rem' }}>
          <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 1rem', borderRadius: '12px', background: 'var(--skeuo-bg)', boxShadow: 'var(--skeuo-outset-shadow)' }}>
            <span style={{ fontSize: '1.75rem' }}>📈</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)', letterSpacing: '-0.04em', textShadow: '1px 1px 0px white' }}>
              Nifty<span style={{ color: 'var(--primary-600)' }}>Signal</span>
            </span>
          </Link>

          <div className="flex items-center gap-4 mobile-hide skeuo-recessed" style={{ padding: '0.4rem 0.6rem', borderRadius: '14px' }}>
            {isAuthenticated && (
              <>
                <NavLink href="/dashboard" active={isActive('/dashboard')}>Terminal</NavLink>
                <NavLink href="/portfolio" active={isActive('/portfolio')}>Portfolio</NavLink>
                <NavLink href="/goal-optimizer" active={isActive('/goal-optimizer')}>Strategies</NavLink>
              </>
            )}
          </div>

          <div className="flex items-center gap-6">
            {isAuthenticated ? (
              <>
                <div className="skeuo-recessed mobile-hide" style={{ padding: '0.5rem 1rem', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', gap: '0.6rem', fontWeight: 800, fontSize: '0.75rem', letterSpacing: '0.05em' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-500)', boxShadow: '0 0 10px var(--accent-500), inset -1px -1px 2px rgba(0,0,0,0.3)' }} />
                  PRO TERMINAL
                </div>
                <button onClick={handleLogout} className="skeuo-button" style={{ padding: '0.65rem 1.25rem', color: '#ef4444' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
                  </svg>
                  <span className="mobile-hide">EXIT</span>
                </button>
              </>
            ) : (
              <>
                <Link href="/login" style={{ color: 'var(--slate-600)', fontWeight: 800, textDecoration: 'none', fontSize: '0.9rem', padding: '0.5rem 1rem' }}>SIGN IN</Link>
                <Link href="/signup" className="skeuo-button" style={{ padding: '0.75rem 1.5rem', background: 'var(--primary-600)', color: 'white' }}>
                  GET STARTED
                </Link>
              </>
            )}

            {/* Mobile Menu Button */}
            <button
              className="skeuo-button mobile-only"
              style={{ padding: '0.5rem' }}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                {mobileMenuOpen ? <path d="M18 6L6 18M6 6l12 12" /> : <path d="M3 12h18M3 6h18M3 18h18" />}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="skeuo-card" style={{ position: 'absolute', top: '100%', left: '1rem', right: '1rem', marginTop: '1rem', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="skeuo-button" style={{ justifyContent: 'flex-start' }}>Terminal</Link>
                <Link href="/portfolio" className="skeuo-button" style={{ justifyContent: 'flex-start' }}>Portfolio</Link>
                <Link href="/goal-optimizer" className="skeuo-button" style={{ justifyContent: 'flex-start' }}>Strategies</Link>
                <button onClick={handleLogout} className="skeuo-button" style={{ color: '#dc2626', justifyContent: 'flex-start' }}>Exit Terminal</button>
              </>
            ) : (
              <>
                <Link href="/login" className="skeuo-button" style={{ justifyContent: 'flex-start' }}>Sign In</Link>
                <Link href="/signup" className="skeuo-button" style={{ background: 'var(--primary-600)', color: 'white' }}>Get Started</Link>
              </>
            )}
          </div>
        )}
      </nav>
      {/* Spacer */}
      <div style={{ height: '80px' }} />
    </>
  )
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link href={href} style={{
      padding: '0.6rem 1.2rem',
      borderRadius: 'var(--radius-md)',
      fontSize: '0.85rem',
      fontWeight: 800,
      textDecoration: 'none',
      color: active ? 'var(--primary-600)' : 'var(--slate-500)',
      background: 'var(--skeuo-bg)',
      boxShadow: active
        ? 'inset 4px 4px 8px var(--skeuo-shadow-dark), inset -4px -4px 8px var(--skeuo-shadow-light)'
        : 'none',
      transition: 'all 0.2s ease',
      textTransform: 'uppercase',
      letterSpacing: '0.05em'
    }}>
      {children}
    </Link>
  )
}

