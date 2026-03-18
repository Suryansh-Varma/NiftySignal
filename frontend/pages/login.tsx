'use client'
import React, { useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useAuth } from '../lib/auth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { signIn } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await signIn(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-in" style={{ minHeight: '100vh', display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 1fr', backgroundColor: 'var(--skeuo-bg)' }}>
      {/* Left side - Tactical Branding */}
      <div className="mobile-hide" style={{
        background: 'linear-gradient(135deg, var(--slate-800) 0%, var(--slate-900) 100%)',
        padding: '5rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle background element */}
        <div style={{ position: 'absolute', top: '-10%', right: '-10%', width: '400px', height: '400px', background: 'var(--primary-500)', opacity: 0.1, filter: 'blur(100px)', borderRadius: '50%' }}></div>

        <div style={{ position: 'relative', zIndex: 10, maxWidth: '440px' }}>
          <Link href="/" className="flex items-center gap-3" style={{ textDecoration: 'none', marginBottom: '4rem' }}>
            <span className="skeuo-knob" style={{ width: '40px', height: '40px' }}></span>
            <span style={{ fontSize: '2rem', fontWeight: 900, color: 'white', letterSpacing: '-0.02em' }}>NiftySignal</span>
          </Link>

          <h1 style={{ fontSize: '3.5rem', fontWeight: 900, color: 'white', lineHeight: 1.1, marginBottom: '2rem' }}>
            Reconnect to the <br />
            <span style={{ color: 'var(--primary-400)' }}>Neural Flux</span>
          </h1>

          <p style={{ fontSize: '1.25rem', color: 'var(--slate-400)', lineHeight: 1.6, marginBottom: '4rem', fontWeight: 600 }}>
            Resume institutional surveillance and execute capital with AI precision.
          </p>

          <div className="flex flex-col gap-5">
            {[
              { icon: '🤖', text: 'Neural Predictions v4.0' },
              { icon: '📊', text: 'Real-time Vault Sync' },
              { icon: '🎯', text: 'Goal Matrix Optimizer' },
            ].map((f, i) => (
              <div key={i} className="skeuo-recessed" style={{ padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(0,0,0,0.2)', border: 'none', boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.4)' }}>
                <span style={{ fontSize: '1.25rem' }}>{f.icon}</span>
                <span style={{ fontSize: '0.9rem', color: 'var(--slate-300)', fontWeight: 700 }}>{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right side - Terminal Interface */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div className="skeuo-card" style={{ width: '100%', maxWidth: '440px', padding: '3.5rem' }}>
          <div style={{ marginBottom: '3rem', textAlign: 'center' }}>
            <h2 style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--slate-800)', marginBottom: '0.5rem' }}>Terminal Login</h2>
            <p style={{ color: 'var(--slate-500)', fontWeight: 700, fontSize: '0.9rem', letterSpacing: '0.05em' }}>ESTABLISH IDENTITY PROTOCOL</p>
          </div>

          {error && (
            <div className="skeuo-recessed" style={{ padding: '1rem', marginBottom: '2rem', background: '#fee2e2', color: '#dc2626', fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem', border: '1px solid #fecaca' }}>
              <span style={{ fontSize: '1.2rem' }}>⚠️</span> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>NEURAL ID (EMAIL)</label>
              <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
                <span style={{ opacity: 0.4 }}>📧</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '1rem', color: 'var(--slate-800)', fontWeight: 600 }}
                  placeholder="operator@vault.ai"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>ACCESS CODE</label>
              <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
                <span style={{ opacity: 0.4 }}>🔑</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '1rem', color: 'var(--slate-800)', fontWeight: 600 }}
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="skeuo-button" style={{
              marginTop: '1.5rem',
              padding: '1.25rem',
              justifyContent: 'center',
              fontSize: '1.1rem',
              fontWeight: 900,
              background: 'linear-gradient(180deg, var(--primary-500) 0%, var(--primary-600) 100%)',
              color: 'white',
              boxShadow: 'var(--skeuo-shadow), 0 10px 20px rgba(79, 70, 229, 0.2)'
            }}>
              {loading ? 'INITIALIZING...' : 'AUTHORIZE ACCESS'}
            </button>
          </form>

          <div className="flex items-center gap-4" style={{ margin: '3rem 0' }}>
            <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.05)' }}></div>
            <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)', letterSpacing: '0.1em' }}>OR</span>
            <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.05)' }}></div>
          </div>

          <Link href="/signup" style={{ textAlign: 'center', display: 'block' }} className="skeuo-button">
            CREATE TERMINAL IDENTITY
          </Link>
        </div>
      </div>
    </div>
  )
}
