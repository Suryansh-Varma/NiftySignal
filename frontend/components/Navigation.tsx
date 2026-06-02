import React, { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '../lib/auth'

export default function Navigation() {
  const { isAuthenticated, signOut } = useAuth()
  const router = useRouter()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const firstMobileLinkRef = useRef<HTMLAnchorElement | null>(null)

  const links = useMemo(
    () => [
      { href: '/dashboard', label: 'Dashboard' },
      { href: '/portfolio', label: 'Portfolio' },
      { href: '/goal-optimizer', label: 'Goal Optimizer' },
    ],
    []
  )

  const handleLogout = async () => {
    try {
      await signOut()
      window.location.href = '/'
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  const isActive = (path: string) => router.pathname === path

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [router.pathname])

  useEffect(() => {
    if (!mobileMenuOpen) return

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileMenuOpen(false)
      }
    }

    document.addEventListener('keydown', onKeyDown)
    firstMobileLinkRef.current?.focus()

    return () => {
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [mobileMenuOpen])

  return (
    <nav
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        borderBottom: '1px solid var(--border-glass)',
        background: 'rgba(5, 7, 10, 0.9)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1280px' }}>
        <div className="flex items-center justify-between" style={{ minHeight: '72px' }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <div className="flex items-center gap-2">
              <span style={{ fontSize: '1.25rem' }}>📈</span>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                NIFTYSIGNAL AI
              </span>
            </div>
          </Link>

          {isAuthenticated && (
            <div className="mobile-hide flex items-center gap-2">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  style={{
                    textDecoration: 'none',
                    padding: '0.55rem 0.9rem',
                    borderRadius: '10px',
                    fontSize: '0.86rem',
                    fontWeight: 700,
                    color: isActive(link.href) ? 'var(--primary-glow)' : 'var(--text-secondary)',
                    background: isActive(link.href) ? 'rgba(0, 255, 204, 0.12)' : 'transparent',
                    border: isActive(link.href) ? '1px solid rgba(0, 255, 204, 0.25)' : '1px solid transparent',
                  }}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          )}

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <span
                  className="mobile-hide"
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: 'var(--text-muted)',
                    border: '1px solid var(--border-glass)',
                    padding: '0.4rem 0.65rem',
                    borderRadius: '999px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                  }}
                >
                  Live Session
                </span>
                <button
                  onClick={handleLogout}
                  style={{
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    background: 'rgba(127, 29, 29, 0.2)',
                    color: '#fca5a5',
                    borderRadius: '10px',
                    padding: '0.52rem 0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link href="/login" style={{ textDecoration: 'none', color: 'var(--text-secondary)', fontWeight: 700, fontSize: '0.9rem' }}>
                  Log in
                </Link>
                <Link
                  href="/signup"
                  style={{
                    textDecoration: 'none',
                    color: '#0b1118',
                    background: 'var(--primary-glow)',
                    borderRadius: '10px',
                    padding: '0.55rem 0.9rem',
                    fontWeight: 800,
                    fontSize: '0.85rem',
                  }}
                >
                  Get Started
                </Link>
              </>
            )}

            {isAuthenticated && (
              <button
                className="mobile-only"
                onClick={() => setMobileMenuOpen((prev) => !prev)}
                style={{
                  border: '1px solid var(--border-glass)',
                  background: 'rgba(15, 23, 42, 0.75)',
                  color: 'var(--text-primary)',
                  borderRadius: '10px',
                  width: '38px',
                  height: '38px',
                  cursor: 'pointer',
                }}
                aria-label="Toggle menu"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-navigation-menu"
              >
                {mobileMenuOpen ? '×' : '☰'}
              </button>
            )}
          </div>
        </div>

        {isAuthenticated && mobileMenuOpen && (
          <div
            id="mobile-navigation-menu"
            className="mobile-only"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              paddingBottom: '1rem',
            }}
            role="menu"
            aria-label="Mobile navigation"
          >
            {links.map((link, index) => (
              <Link
                key={link.href}
                href={link.href}
                ref={index === 0 ? firstMobileLinkRef : undefined}
                onClick={() => setMobileMenuOpen(false)}
                style={{
                  textDecoration: 'none',
                  borderRadius: '10px',
                  border: '1px solid var(--border-glass)',
                  padding: '0.65rem 0.8rem',
                  color: isActive(link.href) ? 'var(--primary-glow)' : 'var(--text-primary)',
                  background: 'rgba(15, 23, 42, 0.75)',
                  fontWeight: 700,
                }}
                role="menuitem"
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  )
}
