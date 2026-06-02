'use client'
import React, { useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useAuth } from '../lib/auth'

export default function Signup() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { signUp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      await signUp(email, password, fullName)
      setSuccess('Account created! Check your email to confirm.')
      setTimeout(() => router.push('/login'), 2000)
    } catch (err: any) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-in" style={{ minHeight: '100vh', display: 'grid', gridTemplateColumns: 'minmax(280px, 1fr) 1fr', backgroundColor: 'var(--skeuo-bg)' }}>
      {/* Left side - Terminal Configuration */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
        <div className="skeuo-card" style={{ width: '100%', maxWidth: '540px', padding: '4rem' }}>
          <Link href="/" className="flex items-center gap-2" style={{ textDecoration: 'none', color: 'var(--slate-400)', fontSize: '0.8rem', fontWeight: 800, marginBottom: '2.5rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            <span style={{ fontSize: '1.2rem' }}>←</span> Return to Base
          </Link>

          <div style={{ marginBottom: '3rem' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--slate-800)', marginBottom: '0.5rem' }}>Create account</h2>
            <p style={{ color: 'var(--slate-500)', fontWeight: 700, fontSize: '0.9rem', letterSpacing: '0.05em' }}>SET UP YOUR PROFILE</p>
          </div>

          {error && (
            <div className="skeuo-recessed" style={{ padding: '1rem', marginBottom: '2rem', background: '#fee2e2', color: '#dc2626', fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem', border: '1px solid #fecaca' }}>
              <span style={{ fontSize: '1.2rem' }}>⚠️</span> {error}
            </div>
          )}

          {success && (
            <div className="skeuo-recessed" style={{ padding: '1rem', marginBottom: '2rem', background: 'var(--accent-50)', color: 'var(--accent-700)', fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem', border: '1px solid var(--accent-100)' }}>
              <span style={{ fontSize: '1.2rem' }}>✅</span> {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>FULL NAME</label>
              <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
                <span style={{ opacity: 0.4 }}>👤</span>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '1rem', color: 'var(--slate-800)', fontWeight: 600 }}
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>EMAIL</label>
              <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
                <span style={{ opacity: 0.4 }}>📧</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '1rem', color: 'var(--slate-800)', fontWeight: 600 }}
                  placeholder="j.doe@network.io"
                />
              </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="flex flex-col gap-2">
                <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>PASSWORD</label>
                <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
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
              <div className="flex flex-col gap-2">
                <label style={{ fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', letterSpacing: '0.1em' }}>CONFIRM PASSWORD</label>
                <div className="skeuo-recessed" style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '1rem', height: '56px' }}>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    style={{ background: 'transparent', border: 'none', outline: 'none', width: '100%', fontSize: '1rem', color: 'var(--slate-800)', fontWeight: 600 }}
                    placeholder="••••••••"
                  />
                </div>
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
              {loading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
            </button>
          </form>

          <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)', textAlign: 'center', marginTop: '2rem', fontWeight: 700 }}>
            BY CONTINUING, YOU AGREE TO THE PLATFORM TERMS
          </p>

          <div className="flex items-center gap-4" style={{ margin: '3rem 0' }}>
            <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.05)' }}></div>
            <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)', letterSpacing: '0.1em' }}>OR</span>
            <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.05)' }}></div>
          </div>

          <Link href="/login" style={{ textAlign: 'center', display: 'block' }} className="skeuo-button">
            LOG IN INSTEAD
          </Link>
        </div>
      </div>

      {/* Right side - Tactical Insight */}
      <div className="mobile-hide" style={{
        background: 'linear-gradient(135deg, var(--slate-800) 0%, var(--slate-900) 100%)',
        padding: '5rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: '440px' }}>
          <div className="skeuo-card" style={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)', padding: '3rem', marginBottom: '3rem' }}>
            <div style={{ color: 'var(--accent-400)', fontSize: '1.5rem', marginBottom: '1.5rem', letterSpacing: '4px' }}>★★★★★</div>
            <p style={{ fontSize: '1.25rem', color: 'white', lineHeight: 1.7, marginBottom: '2.5rem', fontWeight: 600, fontStyle: 'italic' }}>
              "NIFTYSIGNAL AI helped me move beyond traditional indicators. The neural predictions deliver a measurable edge in the Indian markets."
            </p>
            <div className="flex items-center gap-4">
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary-400), var(--primary-600))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 900, fontSize: '1.2rem', boxShadow: '0 4px 15px rgba(0,0,0,0.3)' }}>
                RS
              </div>
              <div>
                <div style={{ color: 'white', fontWeight: 900, fontSize: '1.1rem' }}>Rahul Sharma</div>
                <div style={{ color: 'var(--primary-300)', fontSize: '0.85rem', fontWeight: 800 }}>QUANT OPERATOR</div>
              </div>
            </div>
          </div>

          <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            <div className="skeuo-recessed" style={{ background: 'rgba(255,255,255,0.05)', padding: '2rem', textAlign: 'center' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 900, color: 'white', display: 'block' }}>2K+</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--slate-400)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>NSE INSTRUMENTS</span>
            </div>
            <div className="skeuo-recessed" style={{ background: 'rgba(255,255,255,0.05)', padding: '2rem', textAlign: 'center' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--accent-400)', display: 'block' }}>47%</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--slate-400)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>MODEL ACCURACY</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
